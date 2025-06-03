import os
import time
import pytest # type: ignore
from selenium import webdriver # type: ignore
from selenium.webdriver.common.by import By # type: ignore
from selenium.webdriver.chrome.options import Options # type: ignore
from selenium.webdriver.support.ui import WebDriverWait # type: ignore
from selenium.webdriver.support import expected_conditions as EC # type: ignore
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException # type: ignore

@pytest.fixture(scope="module")
def driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    yield driver
    driver.quit()

def test_resume_ui_flow(driver):
    driver.get("https://ai-resume-checker-nine.vercel.app/")
    wait = WebDriverWait(driver, 30)
    time.sleep(3)
    try:
        job_desc_input = wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR, 'textarea.textarea'
        )))
        job_desc_input.clear()
        job_desc_input.send_keys("Looking for a Software Developer proficient in Python and APIs.")
        print("✅ Job description filled successfully")
    except TimeoutException:
        print("❌ Failed to find job description textarea")
        raise
    try:
        file_input = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, 'input.file-input[type="file"][accept="application/pdf"]'
        )))
        resume_paths = [
            os.path.abspath("tests/sample_resume.pdf"),
            os.path.abspath("tests/sample_resume_2.pdf")
        ]
        for path in resume_paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Resume file not found: {path}")
        for path in resume_paths:
            file_input.send_keys(path)
        print("✅ Resume file uploaded successfully")
        try:
            file_chip = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, '.file-chip'
            )))
            print("✅ File chip displayed, file processed")
        except TimeoutException:
            print("⚠️ File chip not found, but continuing...")
        
        time.sleep(2)
        
    except TimeoutException:
        print("❌ Failed to find file input")
        raise
    try:
        evaluate_button = wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR, 'button.submit-btn:not([disabled])'
        )))
        button_text = evaluate_button.text
        print(f"Button text: {button_text}")
        driver.execute_script("arguments[0].scrollIntoView(true);", evaluate_button)
        time.sleep(1)
        try:
            evaluate_button.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", evaluate_button)
        
        print("✅ Evaluate button clicked successfully")
        
    except TimeoutException:
        print("❌ Evaluate button not found or not clickable")
        print("Current button state:")
        try:
            button = driver.find_element(By.CSS_SELECTOR, 'button.submit-btn')
            print(f"Button disabled: {button.get_attribute('disabled')}")
            print(f"Button text: {button.text}")
        except:
            print("Button not found at all")
        raise
    try:
        loading_button = wait.until(EC.presence_of_element_located((
            By.XPATH, "//button[contains(text(), 'Analyzing')]"
        )))
        print("✅ Loading state detected")
        wait.until(EC.invisibility_of_element_located((
            By.XPATH, "//button[contains(text(), 'Analyzing')]"
        )))
        print("✅ Loading completed")
        
    except TimeoutException:
        print("⚠️ Loading state not detected, continuing...")
    result_found = False
    selectors_to_try = [
        '.results-container',
        '.result-card',
        '.results-header',
        '.results-title',
        '.score-section',
        '.score-card'
    ]
    extended_wait = WebDriverWait(driver, 60)  
    
    for selector in selectors_to_try:
        try:
            print(f"Trying selector: {selector}")
            result_container = extended_wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, selector
            )))
            text = result_container.text.lower()
            result_keywords = ['score', 'result', 'analysis', 'match', 'evaluation', 'resume analysis', 'match score']
            
            if any(keyword in text for keyword in result_keywords):
                result_found = True
                print(f"✅ Results found using selector: {selector}")
                print(f"Result text preview: {text[:200]}...")
                break
                
        except TimeoutException:
            print(f"❌ Selector {selector} not found")
            continue
    
    if not result_found:
        print("⏳ Doing final comprehensive check for results...")
        time.sleep(10)
        try:
            error_element = driver.find_element(By.CSS_SELECTOR, '.error-message')
            print(f"❌ Error found: {error_element.text}")
        except:
            print("No error message found")
        try:
            all_elements = driver.find_elements(By.CSS_SELECTOR, 'div')
            for element in all_elements:
                if element.text and len(element.text) > 50:
                    text = element.text.lower()
                    if any(keyword in text for keyword in ['score', 'analysis', 'resume', 'match']):
                        result_container = element
                        result_found = True
                        print("✅ Results found in comprehensive search")
                        break
        except Exception as e:
            print(f"Error in comprehensive search: {e}")
    
    if not result_found:
        print("❌ No results found. Current page state:")
        print("=" * 80)
        try:
            body_text = driver.find_element(By.TAG_NAME, 'body').text
            print(f"Body text: {body_text[:1000]}...")
        except:
            print("Could not get body text")
            
        print("=" * 80)
        try:
            driver.save_screenshot("test_failure_screenshot.png")
            print("Screenshot saved as test_failure_screenshot.png")
        except:
            pass
            
        raise AssertionError("Result container not found after evaluation")
    result_text = result_container.text
    print(f"✅ Results found. Content preview: {result_text[:300]}...")
    success_indicators = [
        "match score", "resume analysis", "evaluation results", 
        "score", "analysis complete", "/100", "suggested role"
    ]
    
    has_results = any(indicator in result_text.lower() for indicator in success_indicators)
    if not has_results:
        try:
            score_elements = driver.find_elements(By.CSS_SELECTOR, '.score-value')
            if score_elements:
                has_results = True
                print("✅ Found score elements")
        except:
            pass
    
    assert has_results, f"Result container does not contain expected evaluation content. Found: {result_text[:300]}"
    try:
        score_cards = driver.find_elements(By.CSS_SELECTOR, '.score-card')
        if score_cards:
            print(f"✅ Found {len(score_cards)} score cards")
        result_cards = driver.find_elements(By.CSS_SELECTOR, '.result-card')
        if result_cards:
            print(f"✅ Found {len(result_cards)} result cards")
            
    except Exception as e:
        print(f"Error checking specific components: {e}")
    
    print("✅ Test passed successfully!")
    assert True


    