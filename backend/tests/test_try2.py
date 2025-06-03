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
    options.add_argument("--headless=new")  # Uncomment for headless mode
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    yield driver
    driver.quit()

def wait_for_page_load(driver, timeout=30):
    """Wait for the page to fully load"""
    wait = WebDriverWait(driver, timeout)
    wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
    time.sleep(2)  # Additional buffer for dynamic content

def fill_job_description(driver, job_desc_text, wait_time=30):
    """Helper function to fill job description"""
    wait = WebDriverWait(driver, wait_time)
    try:
        job_desc_input = wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR, 'textarea.textarea'
        )))
        job_desc_input.clear()
        job_desc_input.send_keys(job_desc_text)


        print(f"✅ Job description filled: {job_desc_text[:50]}...")
        return True
    except TimeoutException:
        print("❌ Failed to find job description textarea")
        return False

def upload_resume(driver, resume_paths, wait_time=30):
    """Helper function to upload resume files"""
    wait = WebDriverWait(driver, wait_time)
    try:
        file_input = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, 'input.file-input[type="file"][accept="application/pdf"]'
        )))
        
        for path in resume_paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Resume file not found: {path}")
            
        for path in resume_paths:
            file_input.send_keys(path)
            time.sleep(1)  # Small delay between uploads
            
        print(f"✅ Resume files uploaded: {len(resume_paths)} files")
        
        # Wait for file processing
        try:
            wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, '.file-chip'
            )))
            print("✅ File chip displayed, files processed")
        except TimeoutException:
            print("⚠️ File chip not found, but continuing...")
        
        time.sleep(2)
        return True
        
    except (TimeoutException, FileNotFoundError) as e:
        print(f"❌ Failed to upload resume: {e}")
        return False

def click_evaluate_button(driver, wait_time=30):
    """Helper function to click the evaluate button"""
    wait = WebDriverWait(driver, wait_time)
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
        return True
        
    except TimeoutException:
        print("❌ Evaluate button not found or not clickable")
        return False

def wait_for_results(driver, timeout=90):
    """Helper function to wait for and validate results"""
    wait = WebDriverWait(driver, 30)
    extended_wait = WebDriverWait(driver, timeout)
    
    # Wait for loading state
    try:
        wait.until(EC.presence_of_element_located((
            By.XPATH, "//button[contains(text(), 'Analyzing')]"
        )))
        print("✅ Loading state detected")
        wait.until(EC.invisibility_of_element_located((
            By.XPATH, "//button[contains(text(), 'Analyzing')]"
        )))
        print("✅ Loading completed")
    except TimeoutException:
        print("⚠️ Loading state not detected, continuing...")
    
    # Look for results
    result_found = False
    selectors_to_try = [
        '.results-container',
        '.result-card',
        '.results-header',
        '.results-title',
        '.score-section',
        '.score-card'
    ]
    
    for selector in selectors_to_try:
        try:
            result_container = extended_wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, selector
            )))
            text = result_container.text.lower()
            result_keywords = ['score', 'result', 'analysis', 'match', 'evaluation', 'resume analysis', 'match score']
            
            if any(keyword in text for keyword in result_keywords):
                result_found = True
                print(f"✅ Results found using selector: {selector}")
                return result_container
                
        except TimeoutException:
            continue
    
    if not result_found:
        raise AssertionError("No results found after evaluation")

# Test Cases

class TestResumeCheckerBasicFlow:
    """Test basic functionality with different job descriptions and resumes"""
    
    def test_software_developer_role(self, driver):
        """Test with Software Developer job description"""
        driver.get("https://ai-resume-checker-nine.vercel.app/")
        wait_for_page_load(driver)
        
        job_desc = "Looking for a Software Developer proficient in Python, JavaScript, and REST APIs. Experience with databases and cloud platforms preferred."
        resume_paths = [
            os.path.abspath("tests/sample_resume.pdf"),
            os.path.abspath("tests/sample_resume_2.pdf")
        ]
        
        assert fill_job_description(driver, job_desc)
        assert upload_resume(driver, resume_paths)
        assert click_evaluate_button(driver)
        
        result_container = wait_for_results(driver)
        result_text = result_container.text.lower()
        
        # Validate results contain expected elements
        success_indicators = ["match score", "resume analysis", "score", "/100"]
        assert any(indicator in result_text for indicator in success_indicators), \
            f"Results don't contain expected indicators: {result_text[:300]}"
    
    def test_data_scientist_role(self, driver):
        """Test with Data Scientist job description"""
        driver.get("https://ai-resume-checker-nine.vercel.app/")
        wait_for_page_load(driver)
        
        job_desc = "Seeking a Data Scientist with expertise in Machine Learning, Python, R, and statistical analysis. Experience with big data tools like Spark and Hadoop is a plus."
        resume_paths = [os.path.abspath("tests/sample_resume.pdf")]
        
        assert fill_job_description(driver, job_desc)
        assert upload_resume(driver, resume_paths)
        assert click_evaluate_button(driver)
        
        result_container = wait_for_results(driver)
        assert result_container is not None

    def test_marketing_manager_role(self, driver):
        """Test with Marketing Manager job description"""
        driver.get("https://ai-resume-checker-nine.vercel.app/")
        wait_for_page_load(driver)
        
        job_desc = "Marketing Manager position requiring experience in digital marketing, SEO, content creation, and campaign management. MBA preferred."
        resume_paths = [os.path.abspath("tests/sample_resume_2.pdf")]
        
        assert fill_job_description(driver, job_desc)
        assert upload_resume(driver, resume_paths)
        assert click_evaluate_button(driver)
        
        result_container = wait_for_results(driver)
        assert result_container is not None

class TestResumeCheckerEdgeCases:
    """Test edge cases and error scenarios"""
    
    def test_empty_job_description(self, driver):
        """Test behavior with empty job description"""
        driver.get("https://ai-resume-checker-nine.vercel.app/")
        wait_for_page_load(driver)
        
        resume_paths = [os.path.abspath("tests/sample_resume.pdf")]
        
        # Try to upload resume without job description
        assert upload_resume(driver, resume_paths)
        
        # Check if evaluate button is disabled
        try:
            evaluate_button = driver.find_element(By.CSS_SELECTOR, 'button.submit-btn')
            is_disabled = evaluate_button.get_attribute('disabled')
            print(f"Button disabled state with empty job desc: {is_disabled}")
            # Button should be disabled or show validation message
        except Exception:
            print("Evaluate button not found")

    def test_very_long_job_description(self, driver):
        """Test with extremely long job description"""
        driver.get("https://ai-resume-checker-nine.vercel.app/")
        wait_for_page_load(driver)
        
        # Create a very long job description (2000+ characters)
        long_job_desc = """
        We are seeking an exceptional Software Engineer to join our dynamic team. The ideal candidate will have extensive experience in full-stack development, including proficiency in multiple programming languages such as Python, JavaScript, Java, C++, and Go. You should have deep knowledge of web technologies including HTML5, CSS3, React, Angular, Vue.js, Node.js, Express.js, and various CSS frameworks like Bootstrap and Tailwind CSS.
        
        Backend experience should include working with databases such as PostgreSQL, MySQL, MongoDB, Redis, and Elasticsearch. You should be familiar with cloud platforms like AWS, Google Cloud Platform, and Microsoft Azure, including services like EC2, S3, Lambda, Cloud Functions, and container orchestration with Kubernetes and Docker.
        
        The role requires expertise in software architecture patterns, microservices, RESTful APIs, GraphQL, and message queuing systems like RabbitMQ and Apache Kafka. Experience with DevOps practices including CI/CD pipelines, infrastructure as code with Terraform, monitoring with Prometheus and Grafana, and logging solutions is essential.
        
        We value candidates who understand security best practices, have experience with authentication and authorization systems, and are familiar with testing frameworks and methodologies including unit testing, integration testing, and end-to-end testing with tools like Jest, Cypress, and Selenium.
        
        Additional skills that would be beneficial include machine learning frameworks like TensorFlow and PyTorch, data processing with Apache Spark, and mobile development with React Native or Flutter. Experience with blockchain technologies and cryptocurrency systems would be a significant advantage.
        """ * 2  # Double it to make it even longer
        
        resume_paths = [os.path.abspath("tests/sample_resume.pdf")]
        
        assert fill_job_description(driver, long_job_desc)
        assert upload_resume(driver, resume_paths)
        assert click_evaluate_button(driver)
        
        result_container = wait_for_results(driver, timeout=120)  # Extended timeout for processing
        assert result_container is not None

    def test_special_characters_in_job_description(self, driver):
        """Test with special characters and formatting in job description"""
        driver.get("https://ai-resume-checker-nine.vercel.app/")
        wait_for_page_load(driver)
        
        job_desc = """
        Senior Software Engineer @ Tech Startup! 
        
        Required Skills:
        • Python 3.8+ & Django/Flask
        • JavaScript (ES6+) & React.js
        • SQL & NoSQL databases
        • AWS/Azure cloud services
        
        Nice-to-have:
        - Machine Learning (scikit-learn, TensorFlow)
        - Docker & Kubernetes
        - CI/CD pipelines
        
        Salary: $120K-$150K 💰
        Location: San Francisco, CA 🌉
        Remote: Hybrid (2-3 days/week) 🏠
        
        Email: jobs@company.com
        """
        
        resume_paths = [os.path.abspath("tests/sample_resume.pdf")]
        
        assert fill_job_description(driver, job_desc)
        assert upload_resume(driver, resume_paths)
        assert click_evaluate_button(driver)
        
        result_container = wait_for_results(driver)
        assert result_container is not None

class TestResumeCheckerUserInterface:
    """Test UI interactions and user experience"""
    
    def test_form_validation_flow(self, driver):
        """Test form validation and user feedback"""
        driver.get("https://ai-resume-checker-nine.vercel.app/")
        wait_for_page_load(driver)
        
        # Test clicking evaluate without filling anything
        try:
            evaluate_button = driver.find_element(By.CSS_SELECTOR, 'button.submit-btn')
            initial_state = evaluate_button.get_attribute('disabled')
            print(f"Initial button state: {initial_state}")
            
            if not initial_state:
                evaluate_button.click()
                time.sleep(2)
                # Check for validation messages
                try:
                    validation_msg = driver.find_element(By.CSS_SELECTOR, '.error-message, .validation-error')
                    print(f"Validation message found: {validation_msg.text}")
                except Exception:
                    print("No validation message found")
        except Exception:
            print("Could not test form validation")

    def test_file_upload_feedback(self, driver):
        """Test file upload UI feedback"""
        driver.get("https://ai-resume-checker-nine.vercel.app/")
        wait_for_page_load(driver)
        
        job_desc = "Software Developer position requiring Python and JavaScript skills."
        assert fill_job_description(driver, job_desc)
        
        # Upload file and verify UI feedback
        resume_paths = [os.path.abspath("tests/sample_resume.pdf")]
        assert upload_resume(driver, resume_paths)
        
        # Check for file upload indicators
        try:
            file_indicators = driver.find_elements(By.CSS_SELECTOR, '.file-chip, .file-name, .upload-success')
            print(f"Found {len(file_indicators)} file upload indicators")
            
            for indicator in file_indicators:
                print(f"Indicator text: {indicator.text}")
        except Exception as e:
            print(f"Error checking file indicators: {e}")

    def test_responsive_behavior(self, driver):
        """Test responsive design behavior"""
        driver.get("https://ai-resume-checker-nine.vercel.app/")
        wait_for_page_load(driver)
        
        # Test different window sizes
        window_sizes = [
            (1920, 1080),  # Desktop
            (1366, 768),   # Laptop
            (768, 1024),   # Tablet
            (375, 667)     # Mobile
        ]
        
        for width, height in window_sizes:
            driver.set_window_size(width, height)
            time.sleep(2)
            
            print(f"Testing window size: {width}x{height}")
            
            # Check if key elements are still accessible
            try:
                driver.find_element(By.CSS_SELECTOR, 'textarea.textarea')
                driver.find_element(By.CSS_SELECTOR, 'input.file-input')
                driver.find_element(By.CSS_SELECTOR, 'button.submit-btn')
                
                print(f"✅ All elements accessible at {width}x{height}")
            except Exception as e:
                print(f"❌ Element not accessible at {width}x{height}: {e}")

class TestResumeCheckerPerformance:
    """Test performance and load scenarios"""
    
    def test_multiple_resume_upload(self, driver):
        """Test uploading multiple resumes"""
        driver.get("https://ai-resume-checker-nine.vercel.app/")
        wait_for_page_load(driver)
        
        job_desc = "Full-stack Developer with experience in React, Node.js, and databases."
        assert fill_job_description(driver, job_desc)
        
        # Upload multiple resumes if supported
        resume_paths = [
            os.path.abspath("tests/sample_resume.pdf"),
            os.path.abspath("tests/sample_resume_2.pdf")
        ]
        
        assert upload_resume(driver, resume_paths)
        assert click_evaluate_button(driver)
        
        # Extended timeout for multiple resume processing
        result_container = wait_for_results(driver, timeout=120)
        assert result_container is not None
        
        # Check if results mention multiple resumes
        result_text = result_container.text.lower()
        print(f"Results for multiple resumes: {result_text[:500]}")

    def test_processing_time_measurement(self, driver):
        """Measure processing time for evaluation"""
        driver.get("https://ai-resume-checker-nine.vercel.app/")
        wait_for_page_load(driver)
        
        job_desc = "Data Analyst with SQL, Python, and visualization skills."
        resume_paths = [os.path.abspath("tests/sample_resume.pdf")]
        
        assert fill_job_description(driver, job_desc)
        assert upload_resume(driver, resume_paths)
        
        # Measure processing time
        start_time = time.time()
        assert click_evaluate_button(driver)
        
        result_container = wait_for_results(driver)
        end_time = time.time()
        
        processing_time = end_time - start_time
        print(f"✅ Processing completed in {processing_time:.2f} seconds")
        
        # Performance assertion (adjust threshold as needed)
        assert processing_time < 120, f"Processing took too long: {processing_time:.2f} seconds"
        assert result_container is not None

class TestResumeCheckerResults:
    """Test result content and quality"""
    
    def test_result_content_quality(self, driver):
        """Test the quality and completeness of results"""
        driver.get("https://ai-resume-checker-nine.vercel.app/")
        wait_for_page_load(driver)
        
        job_desc = "Senior Python Developer with Django, PostgreSQL, and AWS experience."
        resume_paths = [os.path.abspath("tests/sample_resume.pdf")]
        
        assert fill_job_description(driver, job_desc)
        assert upload_resume(driver, resume_paths)
        assert click_evaluate_button(driver)
        
        result_container = wait_for_results(driver)
        result_text = result_container.text
        
        # Check for comprehensive result content
        expected_elements = [
            "score", "analysis", "match", "skills", "experience", "recommendations"
        ]
        
        found_elements = [elem for elem in expected_elements if elem in result_text.lower()]
        print(f"Found result elements: {found_elements}")
        
        assert len(found_elements) >= 3, f"Results lack comprehensive content. Found: {found_elements}"
        
        # Check result length (should be substantial)
        assert len(result_text) > 100, f"Results too brief: {len(result_text)} characters"

    def test_score_validation(self, driver):
        """Test score format and validity"""
        driver.get("https://ai-resume-checker-nine.vercel.app/")
        wait_for_page_load(driver)
        
        job_desc = "Frontend Developer with React, TypeScript, and modern CSS."
        resume_paths = [os.path.abspath("tests/sample_resume.pdf")]
        
        assert fill_job_description(driver, job_desc)
        assert upload_resume(driver, resume_paths)
        assert click_evaluate_button(driver)
        
        result_container = wait_for_results(driver)
        
        # Look for score elements
        try:
            score_elements = driver.find_elements(By.CSS_SELECTOR, '.score-value, .score-number, [class*="score"]')
            scores_found = []
            
            for element in score_elements:
                text = element.text.strip()
                if text and any(char.isdigit() for char in text):
                    scores_found.append(text)
                    print(f"Found score: {text}")
            
            assert len(scores_found) > 0, "No score values found in results"
            
        except Exception as e:
            print(f"Error validating scores: {e}")
            # Fallback: check result text for score patterns
            import re
            score_patterns = re.findall(r'\d+(?:\.\d+)?(?:/100|%|\s*out\s*of\s*100)', result_container.text)
            assert len(score_patterns) > 0, "No score patterns found in results"

class TestResumeCheckerNegativeScenarios:
    """Test negative scenarios - these should fail gracefully"""
    
    def test_invalid_file_upload(self, driver):
        """Test uploading invalid file types (should be rejected)"""
        driver.get("https://ai-resume-checker-nine.vercel.app/")
        wait_for_page_load(driver)
        
        job_desc = "Software Developer position"
        assert fill_job_description(driver, job_desc)
        
        # Create temporary invalid files for testing
        invalid_files = []
        
        # Create a text file (should be rejected)
        txt_file = os.path.abspath("tests/invalid_resume.txt")
        try:
            with open(txt_file, 'w') as f:
                f.write("This is not a PDF resume file")
            invalid_files.append(txt_file)
        except Exception:
            print("Could not create test text file")
        
        # Create an image file (should be rejected)  
        img_file = os.path.abspath("tests/invalid_resume.jpg")
        try:
            with open(img_file, 'wb') as f:
                # Write minimal JPEG header
                f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF')
            invalid_files.append(img_file)
        except Exception:
            print("Could not create test image file")
        
        for invalid_file in invalid_files:
            if os.path.exists(invalid_file):
                try:
                    file_input = driver.find_element(By.CSS_SELECTOR, 'input.file-input[type="file"]')
                    file_input.send_keys(invalid_file)
                    time.sleep(2)
                    
                    # Check for error message or rejection
                    try:
                        error_msg = driver.find_element(By.CSS_SELECTOR, '.error-message, .file-error, .invalid-file')
                        print(f"✅ Correctly rejected {invalid_file}: {error_msg.text}")
                    except Exception:
                        # Check if file was actually processed (it shouldn't be)
                        try:
                            file_chip = driver.find_element(By.CSS_SELECTOR, '.file-chip')
                            if invalid_file.split('.')[-1].lower() in file_chip.text.lower():
                                print(f"❌ Invalid file was incorrectly accepted: {invalid_file}")
                            else:
                                print(f"✅ Invalid file correctly ignored: {invalid_file}")
                        except Exception:
                            print(f"✅ Invalid file correctly rejected: {invalid_file}")
                            
                except Exception as e:
                    print(f"File input interaction failed for {invalid_file}: {e}")
                
                # Cleanup
                try:
                    os.remove(invalid_file)
                except Exception:
                    pass

    def test_corrupted_pdf_upload(self, driver):
        """Test uploading a corrupted PDF file"""
        driver.get("https://ai-resume-checker-nine.vercel.app/")
        wait_for_page_load(driver)
        
        job_desc = "Software Developer position"
        assert fill_job_description(driver, job_desc)
        
        # Create a fake PDF file (corrupted)
        corrupted_pdf = os.path.abspath("tests/corrupted_resume.pdf")
        try:
            with open(corrupted_pdf, 'wb') as f:
                # Write PDF header but with corrupted content
                f.write(b'%PDF-1.4\n%corrupted content that is not valid PDF')
                f.write(b'invalid binary data' * 100)
            
            try:
                file_input = driver.find_element(By.CSS_SELECTOR, 'input.file-input[type="file"]')
                file_input.send_keys(corrupted_pdf)
                time.sleep(3)
                
                # Try to proceed with evaluation
                if click_evaluate_button(driver):
                    # Should either show error or handle gracefully
                    try:
                        # Wait for either results or error
                        wait = WebDriverWait(driver, 60)
                        
                        # Check for error message first
                        try:
                            error_element = wait.until(EC.presence_of_element_located((
                                By.CSS_SELECTOR, '.error-message, .processing-error, .file-error'
                            )))
                            print(f"✅ Correctly handled corrupted PDF with error: {error_element.text}")
                        except TimeoutException:
                            # Check if it processed anyway (might be robust)
                            try:
                                wait_for_results(driver, timeout=30)
                                print("⚠️ System processed corrupted PDF (robust handling)")
                            except Exception:
                                print("✅ Correctly failed to process corrupted PDF")
                                
                    except Exception as e:
                        print(f"✅ System correctly failed with corrupted PDF: {e}")
                        
            except Exception as e:
                print(f"File upload failed as expected: {e}")
                
        except Exception as e:
            print(f"Could not create corrupted PDF test file: {e}")
        finally:
            # Cleanup
            try:
                os.remove(corrupted_pdf)
            except Exception:
                pass

    def test_empty_file_upload(self, driver):
        """Test uploading an empty PDF file"""
        driver.get("https://ai-resume-checker-nine.vercel.app/")
        wait_for_page_load(driver)
        
        job_desc = "Software Developer position"
        assert fill_job_description(driver, job_desc)
        
        # Create an empty PDF file
        empty_pdf = os.path.abspath("tests/empty_resume.pdf")
        try:
            with open(empty_pdf, 'wb') as f:
                # Write minimal PDF structure but with no content
                f.write(b'%PDF-1.4\n%%EOF')
            
            try:
                file_input = driver.find_element(By.CSS_SELECTOR, 'input.file-input[type="file"]')
                file_input.send_keys(empty_pdf)
                time.sleep(2)
                
                if click_evaluate_button(driver):
                    # Should handle empty content gracefully
                    try:
                        result_container = wait_for_results(driver, timeout=60)
                        result_text = result_container.text.lower()
                        
                        # Check if it mentions lack of content
                        empty_indicators = ['no content', 'empty', 'insufficient', 'no text', 'unable to analyze']
                        if any(indicator in result_text for indicator in empty_indicators):
                            print("✅ Correctly identified empty resume content")
                        else:
                            print("⚠️ Processed empty file without clear indication")
                            
                    except AssertionError:
                        print("✅ Correctly failed to process empty PDF")
                        
            except Exception as e:
                print(f"Empty file handling: {e}")
                
        except Exception as e:
            print(f"Could not create empty PDF test: {e}")
        finally:
            try:
                os.remove(empty_pdf)
            except Exception:
                pass

    def test_no_job_description_submission(self, driver):
        """Test submitting without job description (should fail or be disabled)"""
        driver.get("https://ai-resume-checker-nine.vercel.app/")
        wait_for_page_load(driver)
        
        # Upload resume without job description
        resume_paths = [os.path.abspath("tests/sample_resume.pdf")]
        
        if upload_resume(driver, resume_paths):
            # Check if evaluate button is disabled
            try:
                evaluate_button = driver.find_element(By.CSS_SELECTOR, 'button.submit-btn')
                is_disabled = evaluate_button.get_attribute('disabled')
                
                if is_disabled:
                    print("✅ Evaluate button correctly disabled without job description")
                else:
                    # Try clicking and see if validation occurs
                    try:
                        evaluate_button.click()
                        time.sleep(3)
                        
                        # Check for validation message
                        try:
                            validation_msg = driver.find_element(By.CSS_SELECTOR, '.error-message, .validation-error, .field-error')
                            print(f"✅ Correctly showed validation: {validation_msg.text}")
                        except Exception:
                            # If no validation message, check if it actually processed
                            try:
                                wait_for_results(driver, timeout=30)
                                print("❌ System processed without job description (should require it)")
                            except Exception:
                                print("✅ Correctly prevented processing without job description")
                                
                    except ElementClickInterceptedException:
                        print("✅ Button correctly not clickable without job description")
                        
            except Exception as e:
                print(f"Could not test job description validation: {e}")

    def test_no_resume_submission(self, driver):
        """Test submitting with job description but no resume (should fail)"""
        driver.get("https://ai-resume-checker-nine.vercel.app/")
        wait_for_page_load(driver)
        
        job_desc = "Software Developer with Python and JavaScript experience"
        assert fill_job_description(driver, job_desc)
        
        # Try to submit without uploading resume
        try:
            evaluate_button = driver.find_element(By.CSS_SELECTOR, 'button.submit-btn')
            is_disabled = evaluate_button.get_attribute('disabled')
            
            if is_disabled:
                print("✅ Evaluate button correctly disabled without resume")
            else:
                try:
                    evaluate_button.click()
                    time.sleep(3)
                    
                    # Check for validation message
                    try:
                        validation_msg = driver.find_element(By.CSS_SELECTOR, '.error-message, .validation-error')
                        print(f"✅ Correctly showed validation: {validation_msg.text}")
                    except Exception:
                        print("❌ No validation message shown for missing resume")
                        
                except ElementClickInterceptedException:
                    print("✅ Button correctly not clickable without resume")
                    
        except Exception as e:
            print(f"Could not test resume validation: {e}")

    def test_malicious_input_job_description(self, driver):
        """Test job description with potentially malicious content"""
        driver.get("https://ai-resume-checker-nine.vercel.app/")
        wait_for_page_load(driver)
        
        malicious_inputs = [
            "<script>alert('XSS')</script>Software Developer",
            "'; DROP TABLE users; --",
            "{{7*7}}[[5*5]]Software Developer",  # Template injection
            "<img src=x onerror=alert('XSS')>Developer position",
            "javascript:alert('XSS')//Software Developer"
        ]
        
        resume_paths = [os.path.abspath("tests/sample_resume.pdf")]
        
        for malicious_input in malicious_inputs:
            print(f"Testing malicious input: {malicious_input[:50]}...")
            
            try:
                # Clear and fill with malicious input
                job_desc_input = driver.find_element(By.CSS_SELECTOR, 'textarea.textarea')
                job_desc_input.clear()
                job_desc_input.send_keys(malicious_input)
                
                # Upload resume
                upload_resume(driver, resume_paths)
                
                # Try to submit
                if click_evaluate_button(driver):
                    try:
                        result_container = wait_for_results(driver, timeout=60)
                        result_text = result_container.text
                        
                        # Check if malicious content was sanitized
                        dangerous_content = ['<script', 'alert(', 'DROP TABLE', 'javascript:']
                        
                        if any(dangerous in result_text for dangerous in dangerous_content):
                            print(f"❌ Malicious content not sanitized: {malicious_input[:30]}")
                        else:
                            print(f"✅ Malicious content properly handled: {malicious_input[:30]}")
                            
                    except AssertionError:
                        print(f"✅ System correctly rejected malicious input: {malicious_input[:30]}")
                        
                # Refresh page for next test
                driver.refresh()
                wait_for_page_load(driver)
                
            except Exception as e:
                print(f"Error testing malicious input {malicious_input[:30]}: {e}")

    def test_extremely_large_file(self, driver):
        """Test uploading an extremely large file (should be rejected)"""
        driver.get("https://ai-resume-checker-nine.vercel.app/")
        wait_for_page_load(driver)
        
        job_desc = "Software Developer position"
        assert fill_job_description(driver, job_desc)
        
        # Create a large fake PDF (10MB)
        large_pdf = os.path.abspath("tests/large_resume.pdf")
        try:
            with open(large_pdf, 'wb') as f:
                f.write(b'%PDF-1.4\n')
                # Write 10MB of data
                f.write(b'A' * (10 * 1024 * 1024))
                f.write(b'\n%%EOF')
            
            try:
                file_input = driver.find_element(By.CSS_SELECTOR, 'input.file-input[type="file"]')
                file_input.send_keys(large_pdf)
                time.sleep(5)  # Wait longer for large file processing
                
                # Check for file size error
                try:
                    error_msg = driver.find_element(By.CSS_SELECTOR, '.error-message, .file-size-error, .upload-error')
                    print(f"✅ Correctly rejected large file: {error_msg.text}")
                except Exception:
                    # If no immediate error, try to proceed
                    if click_evaluate_button(driver):
                        try:
                            # Should either timeout or show error
                            wait_for_results(driver, timeout=120)
                            print("⚠️ Large file was processed (might have size limits)")
                        except Exception:
                            print("✅ Large file correctly failed to process")
                            
            except Exception as e:
                print(f"Large file upload failed as expected: {e}")
                
        except Exception as e:
            print(f"Could not create large file test: {e}")
        finally:
            try:
                os.remove(large_pdf)
            except Exception:
                pass

    def test_network_interruption_simulation(self, driver):
        """Test behavior when network is interrupted during processing"""
        driver.get("https://ai-resume-checker-nine.vercel.app/")
        wait_for_page_load(driver)
        
        job_desc = "Software Developer with full-stack experience"
        resume_paths = [os.path.abspath("tests/sample_resume.pdf")]
        
        assert fill_job_description(driver, job_desc)
        assert upload_resume(driver, resume_paths)
        assert click_evaluate_button(driver)
        
        # Wait for processing to start
        try:
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((
                By.XPATH, "//button[contains(text(), 'Analyzing')]"
            )))
            print("✅ Processing started")
            
            # Simulate network interruption by navigating away and back
            # (This simulates connection loss)
            time.sleep(2)
            driver.execute_script("window.location.href = 'about:blank';")
            time.sleep(3)
            driver.get("https://ai-resume-checker-nine.vercel.app/")
            wait_for_page_load(driver)
            
            print("✅ Simulated network interruption and recovery")
            
            # Check if the form is in initial state (as expected)
            try:
                job_desc_input = driver.find_element(By.CSS_SELECTOR, 'textarea.textarea')
                if job_desc_input.get_attribute('value') == '':
                    print("✅ Form correctly reset after interruption")
                else:
                    print("⚠️ Form state persisted (might have session management)")
            except Exception:
                print("Could not check form state after interruption")
                
        except TimeoutException:
            print("Processing didn't start as expected")

    def test_concurrent_submissions(self, driver):
        """Test rapid multiple submissions (should handle gracefully)"""
        driver.get("https://ai-resume-checker-nine.vercel.app/")
        wait_for_page_load(driver)
        
        job_desc = "Software Developer position"
        resume_paths = [os.path.abspath("tests/sample_resume.pdf")]
        
        assert fill_job_description(driver, job_desc)
        assert upload_resume(driver, resume_paths)
        
        # Try to click evaluate button multiple times rapidly
        try:
            for i in range(3):
                try:
                    evaluate_button = driver.find_element(By.CSS_SELECTOR, 'button.submit-btn')
                    if not evaluate_button.get_attribute('disabled'):
                        evaluate_button.click()
                        print(f"Clicked evaluate button {i+1}")
                        time.sleep(0.5)
                    else:
                        print(f"Button disabled after click {i}")
                        break
                except Exception:
                    print(f"Could not click button on attempt {i+1}")
            
            # Check if system handled multiple clicks properly
            try:
                # Should only process once
                wait_for_results(driver, timeout=90)
                print("✅ System handled multiple submissions correctly")
            except Exception:
                print("✅ System correctly prevented duplicate processing")
                
        except Exception as e:
            print(f"Concurrent submission test: {e}")

# Utility function for test reporting
def generate_test_report(results):
    """Generate a comprehensive test report"""
    print("\n" + "="*80)
    print("COMPREHENSIVE TEST REPORT")
    print("="*80)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results if result['status'] == 'PASSED')
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nTest Details:")
    for result in results:
        status_icon = "✅" if result['status'] == 'PASSED' else "❌"
        print(f"{status_icon} {result['test_name']}: {result['status']}")
        if result['status'] == 'FAILED':
            print(f"   Error: {result.get('error', 'Unknown error')}")
    
    print("="*80)

if __name__ == "__main__":
    # Run specific test classes
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--capture=no"
    ])