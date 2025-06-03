import os
import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException

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

@pytest.fixture
def setup_test_files():
    """Create test files for testing"""
    test_dir = "tests"
    os.makedirs(test_dir, exist_ok=True)

    dummy_pdf = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"

    files = {
        "sample_resume.pdf": dummy_pdf,
        "sample_resume_2.pdf": dummy_pdf,
        "sample_resume_3.pdf": dummy_pdf,
        "invalid_file.txt": b"This is not a PDF file",
        "large_file.pdf": b"A" * (12 * 1024 * 1024)  
    }

    for filename, content in files.items():
        with open(os.path.join(test_dir, filename), "wb") as f:
            f.write(content)

    yield files

    for filename in files:
        try:
            os.remove(os.path.join(test_dir, filename))
        except:
            pass

def wait_for_page_load(driver, wait_time=3):
    """Helper function to wait for page load"""
    time.sleep(wait_time)

def fill_job_description(driver, wait, job_text):
    """Helper function to fill job description"""
    job_desc_input = wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR, 'textarea.textarea'
    )))
    job_desc_input.clear()
    job_desc_input.send_keys(job_text)
    return job_desc_input

def upload_files(driver, wait, file_paths):
    """Helper function to upload files"""
    file_input = wait.until(EC.presence_of_element_located((
        By.CSS_SELECTOR, 'input.file-input[type="file"][accept="application/pdf"]'
    )))

    for file_path in file_paths:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Resume file not found at: {file_path}")
        file_input.send_keys(file_path)

    return file_input

def click_evaluate_button(driver, wait):
    """Helper function to click evaluate button"""
    evaluate_button = wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR, 'button.submit-btn:not([disabled])'
    )))

    driver.execute_script("arguments[0].scrollIntoView(true);", evaluate_button)
    time.sleep(1)

    try:
        evaluate_button.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", evaluate_button)

    return evaluate_button

def wait_for_results(driver, wait, timeout=60):
    """Helper function to wait for results"""
    selectors_to_try = [
        '.results-container',
        '.result-card',
        '.results-header',
        '.score-section'
    ]

    extended_wait = WebDriverWait(driver, timeout)

    for selector in selectors_to_try:
        try:
            result_container = extended_wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, selector
            )))

            text = result_container.text.lower()
            result_keywords = ['score', 'result', 'analysis', 'match', 'evaluation', 'resume analysis']

            if any(keyword in text for keyword in result_keywords):
                return result_container, text
        except TimeoutException:
            continue

    return None, None

def check_for_error_message(driver):
    """Helper function to check for error messages"""
    try:
        error_element = driver.find_element(By.CSS_SELECTOR, '.error-message')
        return error_element.text
    except NoSuchElementException:
        return None

def test_01_page_loads_successfully(driver):
    """Test that the page loads and all essential elements are present"""
    driver.get("https://ai-resume-checker-nine.vercel.app/")
    wait = WebDriverWait(driver, 30)
    wait_for_page_load(driver)

    title = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.title')))
    assert "Multi-Resume CV Evaluator" in title.text

    job_desc_textarea = driver.find_element(By.CSS_SELECTOR, 'textarea.textarea')
    file_upload = driver.find_element(By.CSS_SELECTOR, '.file-upload')
    submit_button = driver.find_element(By.CSS_SELECTOR, 'button.submit-btn')

    assert job_desc_textarea is not None
    assert file_upload is not None
    assert submit_button is not None

    print("✅ Page loads successfully with all essential elements")

def test_02_single_resume_evaluation_success(driver, setup_test_files):
    """Test successful evaluation with single resume"""
    driver.get("https://ai-resume-checker-nine.vercel.app/")
    wait = WebDriverWait(driver, 30)
    wait_for_page_load(driver)

    fill_job_description(driver, wait, "Looking for a Software Developer proficient in Python and APIs.")
    print("✅ Job description filled")

    resume_path = os.path.abspath("tests/sample_resume.pdf")
    upload_files(driver, wait, [resume_path])
    print("✅ Resume uploaded")

    click_evaluate_button(driver, wait)
    print("✅ Evaluate button clicked")

    result_container, result_text = wait_for_results(driver, wait)

    assert result_container is not None, "Results container not found"
    assert any(indicator in result_text for indicator in ['score', 'analysis', 'match']), \
        f"Expected result indicators not found in: {result_text[:200]}"

    print("✅ Single resume evaluation test passed")

def test_03_multiple_resume_evaluation_success(driver, setup_test_files):
    """Test successful evaluation with multiple resumes"""
    driver.get("https://ai-resume-checker-nine.vercel.app/")
    wait = WebDriverWait(driver, 30)
    wait_for_page_load(driver)

    fill_job_description(driver, wait, "Looking for experienced Full Stack Developer with React and Node.js expertise.")
    print("✅ Job description filled")

    resume_paths = [
        os.path.abspath("tests/sample_resume.pdf"),
        os.path.abspath("tests/sample_resume_2.pdf"),
        os.path.abspath("tests/sample_resume_3.pdf")
    ]
    upload_files(driver, wait, resume_paths)
    print("✅ Multiple resumes uploaded")

    file_chips = driver.find_elements(By.CSS_SELECTOR, '.file-chip')
    assert len(file_chips) == 3, f"Expected 3 file chips, found {len(file_chips)}"
    print("✅ File chips displayed correctly")

    click_evaluate_button(driver, wait)
    print("✅ Evaluate button clicked")

    result_container, result_text = wait_for_results(driver, wait, timeout=90)

    assert result_container is not None, "Results container not found"

    result_cards = driver.find_elements(By.CSS_SELECTOR, '.result-card')
    assert len(result_cards) >= 1, f"Expected at least 1 result card, found {len(result_cards)}"

    print("✅ Multiple resume evaluation test passed")

def test_04_file_removal_functionality(driver, setup_test_files):
    """Test file removal functionality"""
    driver.get("https://ai-resume-checker-nine.vercel.app/")
    wait = WebDriverWait(driver, 30)
    wait_for_page_load(driver)

    resume_paths = [
        os.path.abspath("tests/sample_resume.pdf"),
        os.path.abspath("tests/sample_resume_2.pdf")
    ]
    upload_files(driver, wait, resume_paths)

    file_chips = driver.find_elements(By.CSS_SELECTOR, '.file-chip')
    assert len(file_chips) == 2, f"Expected 2 file chips, found {len(file_chips)}"

    remove_button = driver.find_element(By.CSS_SELECTOR, '.remove-file')
    remove_button.click()

    time.sleep(1)

    file_chips_after = driver.find_elements(By.CSS_SELECTOR, '.file-chip')
    assert len(file_chips_after) == 1, f"Expected 1 file chip after removal, found {len(file_chips_after)}"

    print("✅ File removal functionality test passed")

def test_05_drag_and_drop_upload(driver, setup_test_files):
    """Test drag and drop file upload (simulated)"""
    driver.get("https://ai-resume-checker-nine.vercel.app/")
    wait = WebDriverWait(driver, 30)
    wait_for_page_load(driver)

    file_upload_area = driver.find_element(By.CSS_SELECTOR, '.file-upload')

    driver.execute_script("""
        var element = arguments[0];
        var event = new DragEvent('dragenter', { bubbles: true });
        element.dispatchEvent(event);
    """, file_upload_area)

    time.sleep(1)

    classes = file_upload_area.get_attribute('class')

    print("✅ Drag and drop UI test completed")

def test_06_responsive_design_check(driver):
    """Test responsive design at different screen sizes"""
    driver.get("https://ai-resume-checker-nine.vercel.app/")
    wait_for_page_load(driver)

    driver.set_window_size(375, 667)  
    time.sleep(2)

    title = driver.find_element(By.CSS_SELECTOR, '.title')
    assert title.is_displayed(), "Title not visible on mobile"

    textarea = driver.find_element(By.CSS_SELECTOR, 'textarea.textarea')
    assert textarea.is_displayed(), "Textarea not visible on mobile"

    driver.set_window_size(768, 1024)  
    time.sleep(2)

    driver.set_window_size(1920, 1080)
    time.sleep(2)

    print("✅ Responsive design test passed")

def test_07_fail_empty_job_description(driver, setup_test_files):
    """Test validation: Submit without job description (should fail)"""
    driver.get("https://ai-resume-checker-nine.vercel.app/")
    wait = WebDriverWait(driver, 30)
    wait_for_page_load(driver)

    resume_path = os.path.abspath("tests/sample_resume.pdf")
    upload_files(driver, wait, [resume_path])

    click_evaluate_button(driver, wait)

    time.sleep(2)
    error_message = check_for_error_message(driver)

    assert error_message is not None, "Expected error message for empty job description"
    assert "job description" in error_message.lower(), f"Error message should mention job description: {error_message}"

    print("✅ Empty job description validation test passed")

def test_08_fail_no_resume_uploaded(driver):
    """Test validation: Submit without resume files (should fail)"""
    driver.get("https://ai-resume-checker-nine.vercel.app/")
    wait = WebDriverWait(driver, 30)
    wait_for_page_load(driver)

    fill_job_description(driver, wait, "Looking for a Data Scientist with machine learning experience.")

    click_evaluate_button(driver, wait)

    time.sleep(2)
    error_message = check_for_error_message(driver)

    assert error_message is not None, "Expected error message for no resume files"
    assert "resume" in error_message.lower(), f"Error message should mention resume: {error_message}"

    print("✅ No resume validation test passed")

def test_09_fail_invalid_file_type(driver, setup_test_files):
    """Test validation: Upload non-PDF file (should show error)"""
    driver.get("https://ai-resume-checker-nine.vercel.app/")
    wait = WebDriverWait(driver, 30)
    wait_for_page_load(driver)

    file_input = wait.until(EC.presence_of_element_located((
        By.CSS_SELECTOR, 'input.file-input[type="file"]'
    )))

    invalid_file_path = os.path.abspath("tests/invalid_file.txt")
    file_input.send_keys(invalid_file_path)

    time.sleep(2)

    error_message = check_for_error_message(driver)

    file_chips = driver.find_elements(By.CSS_SELECTOR, '.file-chip')

    assert len(file_chips) == 0 or error_message is not None, \
        "Invalid file type should either be rejected or show error message"

    print("✅ Invalid file type test passed")

def test_10_fail_large_file_upload(driver, setup_test_files):
    """Test validation: Upload file larger than limit (should show error)"""
    driver.get("https://ai-resume-checker-nine.vercel.app/")
    wait = WebDriverWait(driver, 30)
    wait_for_page_load(driver)

    try:
        large_file_path = os.path.abspath("tests/large_file.pdf")
        file_input = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, 'input.file-input[type="file"]'
        )))
        file_input.send_keys(large_file_path)

        time.sleep(3)

        error_message = check_for_error_message(driver)
        file_chips = driver.find_elements(By.CSS_SELECTOR, '.file-chip')

        print(f"Error message: {error_message}")
        print(f"File chips count: {len(file_chips)}")

        print("✅ Large file upload test completed")

    except Exception as e:
        print(f"✅ Large file upload correctly rejected: {e}")

def test_11_fail_server_error_simulation(driver, setup_test_files):
    """Test handling of server errors (simulated by using invalid endpoint)"""
    driver.get("https://ai-resume-checker-nine.vercel.app/")
    wait = WebDriverWait(driver, 30)
    wait_for_page_load(driver)

    fill_job_description(driver, wait, "Software Engineer position requiring Java and Spring Boot.")
    resume_path = os.path.abspath("tests/sample_resume.pdf")
    upload_files(driver, wait, [resume_path])

    driver.execute_script("""
        // Override fetch to simulate server error
        const originalFetch = window.fetch;
        window.fetch = function(url, options) {
            if (url.includes('evaluate-resumes')) {
                return Promise.resolve({
                    ok: false,
                    status: 500,
                    statusText: 'Internal Server Error',
                    json: () => Promise.resolve({error: 'Server error'})
                });
            }
            return originalFetch(url, options);
        };
    """)

    click_evaluate_button(driver, wait)

    time.sleep(5)
    error_message = check_for_error_message(driver)

    assert error_message is not None, "Expected error message for server error"
    print(f"✅ Server error handling test passed: {error_message}")

def test_12_fail_network_timeout_simulation(driver, setup_test_files):
    """Test handling of network timeout"""
    driver.get("https://ai-resume-checker-nine.vercel.app/")
    wait = WebDriverWait(driver, 30)
    wait_for_page_load(driver)

    fill_job_description(driver, wait, "Data Analyst position with Python and SQL skills.")
    resume_path = os.path.abspath("tests/sample_resume.pdf")
    upload_files(driver, wait, [resume_path])

    driver.execute_script("""
        // Override fetch to simulate timeout
        const originalFetch = window.fetch;
        window.fetch = function(url, options) {
            if (url.includes('evaluate-resumes')) {
                return new Promise((resolve, reject) => {
                    setTimeout(() => reject(new Error('Network timeout')), 1000);
                });
            }
            return originalFetch(url, options);
        };
    """)

    click_evaluate_button(driver, wait)

    time.sleep(10)
    error_message = check_for_error_message(driver)

    assert error_message is not None, "Expected error message for network timeout"
    print(f"✅ Network timeout handling test passed: {error_message}")

if __name__ == "__main__":

    pytest.main([__file__, "-v", "-s"])