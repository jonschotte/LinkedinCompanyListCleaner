import io
import time
import pandas as pd
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Streamlit app
st.title("LinkedIn Industry Scraper")

# App description button
if st.button("What does this app do?"):
    st.info(
        """This app allows you to upload an Excel file containing a list of companies. 
        It will search for each company's LinkedIn page, extract the industry information, 
        and provide a downloadable Excel file with the results. 
        You will need to enter your LinkedIn credentials before running the scraper."""
    )

st.write("Upload an Excel file with a 'Company' column to extract LinkedIn industry data.")

# Instructions for the uploaded file
st.markdown(
    """### File Requirements:
    - The file must be in **Excel (.xlsx) format**.
    - It must contain a column named **'Company'**.
    - Other optional columns (if not present, they will be added):
      - **Industry** (will be filled with extracted industry information)
      - **LinkedIn URL** (will store the LinkedIn profile link of the company)
    """
)

# User input for LinkedIn credentials
username = st.text_input("LinkedIn Username", type="default")
password = st.text_input("LinkedIn Password", type="password")

# File uploader
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file and username and password and st.button("Run Scraper"):
    df = pd.read_excel(uploaded_file)
    if "Company" not in df.columns:
        st.error("The uploaded file must contain a 'Company' column.")
    else:
        # Add missing columns if not present
        if "Industry" not in df.columns:
            df["Industry"] = None
        if "LinkedIn URL" not in df.columns:
            df["LinkedIn URL"] = None

        # Ensure Chromium is installed
        CHROME_BIN = "/usr/bin/chromium"
        CHROMEDRIVER_BIN = "/usr/bin/chromedriver"

        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run without GUI
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.binary_location = CHROME_BIN

        # Start WebDriver using Chromium
        driver = webdriver.Chrome(service=Service(CHROMEDRIVER_BIN), options=chrome_options)


        # LinkedIn login function
        def linkedin_login():
            driver.get("https://www.linkedin.com/login")
            time.sleep(3)
            driver.find_element("id", "username").send_keys(username)
            driver.find_element("id", "password").send_keys(password)
            driver.find_element("id", "password").send_keys("\n")
            time.sleep(5)


        linkedin_login()


        # Search and extract LinkedIn data
        def search_company(company_name):
            driver.get("https://www.google.com")
            time.sleep(2)
            search_box = driver.find_element("name", "q")
            search_box.send_keys(f"{company_name} LinkedIn")
            search_box.send_keys("\n")
            time.sleep(3)
            try:
                first_result = driver.find_element("xpath", "(//h3)[1]")
                first_result.click()
                time.sleep(2)
                current_url = driver.current_url
                if "company" in current_url:
                    try:
                        industry_element = driver.find_element("class name", "org-top-card-summary__title")
                        industry = industry_element.get_attribute("title")
                        return industry, current_url
                    except:
                        return "Unknown Industry", current_url
                else:
                    return "No Company Page", current_url
            except:
                return "No Results", ""


        # Processing loop with progress updates
        progress_bar = st.progress(0)
        status_text = st.empty()
        total_companies = len(df)
        processed_count = 0

        for index, row in df.iterrows():
            if pd.notna(row["Industry"]):
                continue  # Skip if already processed
            industry, url = search_company(row["Company"])
            df.at[index, "Industry"] = industry
            df.at[index, "LinkedIn URL"] = url

            processed_count += 1
            progress_bar.progress(int((processed_count / total_companies) * 100))
            status_text.text(f"Processing: {row['Company']} ({processed_count}/{total_companies})")

        driver.quit()

        # Save the updated data to an Excel file
        output =io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)

        # Provide a download link
        st.download_button(
            label="Download Updated Excel File",
            data=output,
            file_name="updated_companies.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.success("Processing complete! Download the updated file.")