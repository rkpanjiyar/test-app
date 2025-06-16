import streamlit as st
import requests
from bs4 import BeautifulSoup
import json

def get_page_content(url):
    """
    Fetches the HTML content from a given URL.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10) # Add timeout
        response.raise_for_status() # Raise an HTTPError for bad responses
        return response.text
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching {url}: {e}")
        return None


def extract_symptoms_section(html_content):
    """
    Extracts text from potential symptom sections of a Wikipedia page.
    Looks for headings like 'Symptoms' or 'Signs and symptoms'.
    """
    if not html_content:
        return ""


    soup = BeautifulSoup(html_content, 'html.parser')
    symptoms_text = []


    # Common headings for symptom sections on Wikipedia
    potential_symptom_headings = [
        "Symptoms",
        "Signs and symptoms",
        "Clinical presentation",
        "Characteristics" # Sometimes symptoms are described under this
    ]


    # Iterate through different heading levels
    for tag_name in ['h2', 'h3', 'h4']:
        for heading_text in potential_symptom_headings:
            # Find the heading element
            heading = soup.find(tag_name, string=lambda text: text and heading_text.lower() in text.lower())


            if heading:
                # Iterate through siblings until the next heading of the same or higher level
                # to get all content under the symptom section
                current_element = heading.find_next_sibling()
                while current_element:
                    if current_element.name and current_element.name.startswith('h') and \
                       int(current_element.name[1]) <= int(tag_name[1]):
                        break # Stop if a new heading of same or higher level is found
                    if current_element.name not in ['sup', 'a', 'span']: # Exclude reference tags etc.
                        symptoms_text.append(current_element.get_text(separator=' ', strip=True))
                    current_element = current_element.find_next_sibling()
                if symptoms_text: # If we found content, stop looking
                    return " ".join(symptoms_text)
    return ""


def extract_description(html_content):
    """
    Extracts the first few relevant paragraphs as a description from a Wikipedia page.
    """
    if not html_content:
        return "No description available."


    soup = BeautifulSoup(html_content, 'html.parser')

    description_paragraphs = []
    # Find all top-level paragraphs (direct children of body or div.mw-parser-output)
    # Wikipedia descriptions are usually in the first few <p> tags.
    paragraphs = soup.find('div', class_='mw-parser-output').find_all('p', recursive=False, limit=3) if soup.find('div', class_='mw-parser-output') else soup.find_all('p', limit=3)


    for p in paragraphs:
        text = p.get_text(separator=' ', strip=True)
        # Exclude paragraphs that are too short, or look like disambiguation/nav warnings
        if text and len(text.split()) > 5 and not text.lower().startswith("for other uses, see"):
            description_paragraphs.append(text)

    return " ".join(description_paragraphs) if description_paragraphs else "No description available."


def check_shared_symptoms_and_description(page_url, your_symptoms):
    """
    Fetches Wikipedia page, extracts symptom section, counts shared symptoms,
    and extracts a brief description.
    """
    html_content = get_page_content(page_url)
    if not html_content:
        return "N/A", [], "Error: Could not fetch page content."


    # Extract raw text for symptom matching
    page_symptoms_raw_text = extract_symptoms_section(html_content).lower()

    # Fallback for symptom text if no explicit section found
    if not page_symptoms_raw_text:
        soup_temp = BeautifulSoup(html_content, 'html.parser')
        first_paragraphs_for_symptoms = soup_temp.find_all('p', limit=3)
        page_symptoms_raw_text = " ".join([p.get_text().lower() for p in first_paragraphs_for_symptoms])


    shared_count = 0
    found_symptoms = []


    your_symptoms_lower = [s.lower() for s in your_symptoms]


    for symptom in your_symptoms_lower:
        if symptom in page_symptoms_raw_text:
            shared_count += 1
            found_symptoms.append(symptom)

    # Specific adjustment for Alzheimer's/Dementia
    if "alzheimer" in page_url.lower() and "dementia" not in found_symptoms and "dementia" in page_symptoms_raw_text:
         shared_count += 1
         found_symptoms.append("dementia")


    # Extract description
    description = extract_description(html_content)


    return shared_count, found_symptoms, description

# --- Streamlit Application ---

st.set_page_config(page_title="Medical Symptom Checker", layout="wide")
st.title("Medical Symptom Checker")
st.markdown("Enter your symptoms and explore potential medical conditions based on Wikipedia data.")

# User input for symptoms
st.header("Your Symptoms")
my_symptoms_input = st.text_area(
    "Enter your symptoms, separated by commas (e.g., fatigue, fever, headache)",
    "fatigue, fever, headache, cough, shortness of breath, muscle pain, joint pain, nausea, vomiting, weight loss"
)

# Process user symptoms
my_symptoms = [s.strip() for s in my_symptoms_input.split(',') if s.strip()]
st.write(f"You entered: {', '.join(my_symptoms)}")

# Dictionary of disease names and their corresponding Wikipedia URLs
wikipedia_pages = {
    "Cardiovascular Diseases": "https://en.wikipedia.org/wiki/Cardiovascular_disease",
    "Cancers": "https://en.wikipedia.org/wiki/Cancer",
    "Chronic Obstructive Pulmonary Disease (COPD)": "https://en.wikipedia.org/wiki/Chronic_obstructive_pulmonary_disease",
    "Lower Respiratory Infections": "https://en.wikipedia.org/wiki/Lower_respiratory_tract_infection",
    "Diabetes Mellitus": "https://en.wikipedia.org/wiki/Diabetes_mellitus",
    "Alzheimer's Disease and Other Dementias": "https://en.wikipedia.org/wiki/Alzheimer%27s_disease",
    "Diarrheal Diseases": "https://en.wikipedia.org/wiki/Diarrhea",
    "Kidney Diseases": "https://en.wikipedia.org/wiki/Kidney_disease",
    "Tuberculosis (TB)": "https://en.wikipedia.org/wiki/Tuberculosis",
    "Road Injuries": "https://en.wikipedia.org/wiki/Traffic_collision",
    "HIV/AIDS": "https://en.wikipedia.org/wiki/HIV/AIDS",
    "Malaria": "https://en.wikipedia.org/wiki/Malaria",
    "Neglected Tropical Diseases (NTDs)": "https://en.wikipedia.org/wiki/Neglected_tropical_diseases",
    "Mental Disorder": "https://en.wikipedia.org/wiki/Mental_disorder",
    "Substance Use Disorder": "https://en.wikipedia.org/wiki/Substance_use_disorder",
    "Musculoskeletal Disorders": "https://en.wikipedia.org/wiki/Musculoskeletal_disorder",
    "Preterm Birth Complications": "https://en.wikipedia.org/wiki/Preterm_birth",
    "Obesity": "https://en.wikipedia.org/wiki/Obesity",
    "Oral Diseases": "https://en.wikipedia.org/wiki/Oral_disease",
    "Liver Diseases": "https://en.wikipedia.org/wiki/Liver_disease",
    "Hypertensive Heart Disease": "https://en.wikipedia.org/wiki/Hypertensive_heart_disease",
    "Birth Asphyxia": "https://en.wikipedia.org/wiki/Birth_asphyxia",
    "Birth Trauma": "https://en.wikipedia.org/wiki/Birth_trauma",
    "Congenital Anomalies": "https://en.wikipedia.org/wiki/Congenital_anomaly",
    "Foodborne Illness": "https://en.wikipedia.org/wiki/Foodborne_illness",
    "Dengue": "https://en.wikipedia.org/wiki/Dengue_fever",
    "Self-harm": "https://en.wikipedia.org/wiki/Self-harm",
    "Suicide": "https://en.wikipedia.org/wiki/Suicide"
}


if st.button("Analyze Symptoms"):
    if not my_symptoms:
        st.warning("Please enter at least one symptom.")
    else:
        st.info("Processing Wikipedia pages to check shared symptoms and extract descriptions... This may take a moment.")
        results_list = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        total_pages = len(wikipedia_pages)
        for i, (disease_category, url) in enumerate(wikipedia_pages.items()):
            status_text.text(f"Processing {disease_category} ({i+1}/{total_pages})...")
            shared_count, found_symptoms, description = check_shared_symptoms_and_description(url, my_symptoms)

            # Get the official page title
            page_title = ""
            if isinstance(description, str) and description.startswith("Error"):
                page_title = disease_category # Use category name if description indicates an error
            else:
                html_content_for_title = get_page_content(url)
                if html_content_for_title:
                    soup_for_title = BeautifulSoup(html_content_for_title, 'html.parser')
                    title_span = soup_for_title.find('span', class_='mw-page-title-main')
                    if title_span:
                        page_title = title_span.get_text(strip=True)
                    else:
                        page_title = disease_category + " (Title Not Found)"
                else:
                    page_title = disease_category + " (Page Not Accessible)"

            if shared_count != 0:
                results_list.append({
                    "disease_category": disease_category,
                    "wikipedia_page_title": page_title,
                    "wikipedia_url": url,
                    "shared_symptoms_count": shared_count,
                    "found_symptoms": found_symptoms,
                    "description": description
                })
            progress_bar.progress((i + 1) / total_pages)

        status_text.text("Analysis complete!")
        progress_bar.empty()

        results_list.sort(key=lambda x: x["shared_symptoms_count"], reverse=True)

        st.header("Analysis Results")

        if not results_list:
            st.warning("No matching diseases found for your symptoms.")
        else:
            for result in results_list:
                st.subheader(f"{result['wikipedia_page_title']} ({result['disease_category']})")
                st.markdown(f"**Shared Symptoms Count:** {result['shared_symptoms_count']}")
                if result['found_symptoms']:
                    st.markdown(f"**Found Symptoms:** {', '.join(result['found_symptoms'])}")
                else:
                    st.markdown("**Found Symptoms:** None explicitly matched in the extracted sections.")
                st.markdown(f"**Description:** {result['description']}")
                st.markdown(f"**Wikipedia Link:** [Read more]({result['wikipedia_url']})")
                st.markdown("---")
