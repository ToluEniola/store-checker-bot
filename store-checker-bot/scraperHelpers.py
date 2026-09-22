from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import time

VALID_SIZES = (
    ["XS", "S", "M", "L", "XL", "XXL", "2XL", "3XL"] +
    [str(i) for i in range(28, 41)] +  # jeans waist
    [str(i) for i in range(6, 14)]     # UK shoes
)

def _accept_cookies(driver, timeout=8):
    try:
        wait = WebDriverWait(driver, timeout)
        btn = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
        btn.click()
        print("Cookie alert closed.")
        time.sleep(1)
    except:
        print("No cookie alert.")

def _brute_force_sizes(driver, sizes_to_check):
    """Scan every element on the page and return stock status for requested sizes."""
    all_elements = driver.find_elements(By.XPATH, "//*")

    # Group all elements by their size text
    size_candidates = {s: [] for s in sizes_to_check}
    for elem in all_elements:
        try:
            text = elem.text.strip()
            if text in sizes_to_check:
                size_candidates[text].append(elem)
        except:
            continue

    sizes_found = {s: False for s in sizes_to_check}
    sizes_in_stock = []

    for size_text, candidates in size_candidates.items():
        if not candidates:
            continue

        sizes_found[size_text] = True

        # Prefer button elements, then elements with role, then fall back to first
        best = None
        for elem in candidates:
            try:
                tag = elem.tag_name
                role = elem.get_attribute("role") or ""
                if tag == "button":
                    best = elem
                    break
                if role in ["button", "option", "radio"] and best is None:
                    best = elem
            except:
                continue
        if best is None:
            best = candidates[0]

        try:
            elem_class = (best.get_attribute("class") or "").lower()
            elem_disabled = best.get_attribute("disabled")
            elem_aria = best.get_attribute("aria-disabled")

            parent_class, parent_disabled, parent_aria = "", None, None
            try:
                parent = best.find_element(By.XPATH, "./..")
                parent_class = (parent.get_attribute("class") or "").lower()
                parent_disabled = parent.get_attribute("disabled")
                parent_aria = parent.get_attribute("aria-disabled")
            except:
                pass

            is_disabled = any([
                any(w in elem_class for w in ['disabled', 'unavailable', 'out-of-stock', 'sold-out']),
                any(w in parent_class for w in ['disabled', 'unavailable', 'out-of-stock', 'sold-out']),
                elem_disabled is not None,
                elem_aria == "true",
                parent_disabled is not None,
                parent_aria == "true",
            ])

            if is_disabled:
                print(f"   ❌ {size_text} out of stock")
            else:
                print(f"   ✅ {size_text} in stock!")
                sizes_in_stock.append(size_text)

        except Exception as e:
            print(f"Error checking {size_text}: {e}")

    if not any(sizes_found.values()):
        print(f"Sizes {', '.join(sizes_to_check)} not found on page.")
        return None

    return sizes_in_stock if sizes_in_stock else False


def check_stock_zara(driver, sizes_to_check):
    try:
        wait = WebDriverWait(driver, 60)
        _accept_cookies(driver)

        try:
            btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-qa-action='add-to-cart']")))
            overlays = driver.find_elements(By.CLASS_NAME, "zds-backdrop")
            if overlays:
                driver.execute_script("arguments[0].remove();", overlays[0])
            driver.execute_script("arguments[0].click();", btn)
            print("Clicked 'Add to Cart'.")
        except (TimeoutException, ElementClickInterceptedException) as e:
            print(f"Failed to click 'Add to Cart': {e}")
            return None

        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "size-selector-sizes")))
        size_elements = driver.find_elements(By.CLASS_NAME, "size-selector-sizes-size")
        sizes_found = {s: False for s in sizes_to_check}
        sizes_in_stock = []

        for li in size_elements:
            try:
                label = li.find_element(By.CSS_SELECTOR, "div[data-qa-qualifier='size-selector-sizes-size-label']").text.strip()
                if label not in sizes_to_check:
                    continue
                sizes_found[label] = True
                button = li.find_element(By.CLASS_NAME, "size-selector-sizes-size__button")
                try:
                    action_text = button.find_element(By.CLASS_NAME, "size-selector-sizes-size__action").text.strip()
                    if "Similar products" in action_text:
                        print(f"{label} out of stock (similar products shown).")
                        continue
                except NoSuchElementException:
                    pass
                if button.get_attribute("data-qa-action") in ["size-in-stock", "size-low-on-stock"]:
                    print(f"{label} in stock.")
                    sizes_in_stock.append(label)
                else:
                    print(f"{label} out of stock.")
            except Exception as e:
                print(f"Error processing Zara size: {e}")

        if not any(sizes_found.values()):
            print(f"Sizes {', '.join(sizes_to_check)} not found.")
            return None
        return sizes_in_stock if sizes_in_stock else False

    except Exception as e:
        print(f"Zara error: {e}")
    return None


def check_stock_bershka(driver, sizes_to_check):
    try:
        wait = WebDriverWait(driver, 15)
        _accept_cookies(driver)

        # Scroll to trigger lazy load
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(1)

        # Wait for product section then click add to basket
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='product']")))
        except:
            pass
        time.sleep(2)

        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                btn_text = (btn.text or "").strip().lower()
                if any(w in btn_text for w in ['add', 'bag', 'cart', 'size', 'select']) and btn.is_displayed():
                    driver.execute_script("arguments[0].click();", btn)
                    print(f"Clicked: {btn.text.strip()}")
                    time.sleep(2)
                    break
        except Exception as e:
            print(f"Button click failed: {e}")

        print("Scanning for sizes...")
        return _brute_force_sizes(driver, sizes_to_check)

    except Exception as e:
        print(f"Bershka error: {e}")
    return None


def check_stock_pullandbear(driver, sizes_to_check):
    try:
        wait = WebDriverWait(driver, 20)
        _accept_cookies(driver)

        # Scroll to trigger lazy load
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(1)

        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'product') or contains(@class, 'detail')]")))
        except:
            pass
        time.sleep(3)

        # Try to click size selector
        clicked = False
        for text in ['select size', 'select', 'size', 'choose size']:
            try:
                btn = driver.find_element(By.XPATH, f"//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]")
                if btn.is_displayed():
                    driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                    driver.execute_script("arguments[0].click();", btn)
                    print(f"Clicked '{btn.text}'")
                    clicked = True
                    time.sleep(2)
                    break
            except:
                continue

        if not clicked:
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    if btn.is_displayed() and btn.text.strip():
                        if any(w in (btn.get_attribute("class") or "").lower() for w in ['cta', 'primary']):
                            driver.execute_script("arguments[0].click();", btn)
                            print(f"Clicked CTA: {btn.text.strip()}")
                            time.sleep(2)
                            break
            except Exception as e:
                print(f"CTA click failed: {e}")

        print("Scanning for sizes...")
        return _brute_force_sizes(driver, sizes_to_check)

    except Exception as e:
        print(f"Pull&Bear error: {e}")
    return None


def check_stock_mango(driver, sizes_to_check):
    try:
        wait = WebDriverWait(driver, 15)
        _accept_cookies(driver)

        try:
            wait.until(EC.any_of(
                EC.presence_of_element_located((By.ID, "pdp-size-selector")),
                EC.presence_of_element_located((By.ID, "pdp-primary-actions"))
            ))
        except TimeoutException:
            print("Mango: size selector not found in time.")
            return None

        size_elements = []
        for sel in ["button[id^='pdp.productInfo.sizeSelector.size']", "p[id^='pdp.productInfo.sizeSelector.size']"]:
            size_elements.extend(driver.find_elements(By.CSS_SELECTOR, sel))

        def extract_label(el):
            try:
                label = el.find_element(By.CSS_SELECTOR, "span.textActionM_className__8McJk").text.strip()
                return "standard" if label.lower() in ["standart", "standard"] else label
            except:
                text = el.text.strip()
                return "standard" if text.lower() in ["standart", "standard"] else text

        if size_elements:
            sizes_found = {s: False for s in sizes_to_check}
            sizes_in_stock = []
            for el in size_elements:
                try:
                    label = extract_label(el)
                    if label not in sizes_to_check:
                        continue
                    sizes_found[label] = True
                    el_id = el.get_attribute("id") or ""
                    available = "sizeAvailable" in el_id and "sizeUnavailable" not in el_id
                    enabled = el.get_attribute("aria-disabled") != "true" and el.get_attribute("disabled") is None
                    if available and enabled:
                        print(f"{label} in stock!")
                        sizes_in_stock.append(label)
                    else:
                        print(f"{label} out of stock.")
                except Exception as e:
                    print(f"Mango size error: {e}")
            if not any(sizes_found.values()):
                print(f"Sizes {', '.join(sizes_to_check)} not found on Mango.")
                return None
            return sizes_in_stock if sizes_in_stock else False

        # No-size product
        if "standard" in sizes_to_check:
            try:
                actions = driver.find_element(By.ID, "pdp-primary-actions")
                add_buttons = actions.find_elements(By.CSS_SELECTOR, "button.ButtonPrimary_default__2Mbr8, button[aria-disabled]") or actions.find_elements(By.TAG_NAME, "button")
                for btn in add_buttons:
                    label = (btn.text or "").strip().lower()
                    if ("add" in label or label == "") and btn.get_attribute("aria-disabled") != "true":
                        print("standard in stock!")
                        return ["standard"]
                print("standard out of stock.")
                return False
            except Exception as e:
                print(f"Mango no-size check failed: {e}")
                return None

        print("No sizes found and 'standard' not requested.")
        return None

    except Exception as e:
        print(f"Mango error: {e}")
    return None