import streamlit as st
import pandas as pd
from openai import OpenAI
import json
from datetime import datetime

st.title("Related Work Organizer based on Zotero CSV")

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["openai_api_key"])

# User guide: Exporting CSV file from Zotero
st.subheader("How to Export CSV File from Zotero")

col1, col2 = st.columns(2)
with col1:
    st.image("zotero_export_step1.png", caption="Step 1: Export Collection")
with col2:
    st.image("zotero_export_step2.png", caption="Step 2: Select CSV Format")

# CSV file upload feature
uploaded_file = st.file_uploader("Upload CSV file exported from Zotero", type=["csv"])

# User's paper Abstract input field
user_abstract = st.text_area("Please enter your paper's Abstract:")

# Submit button
if st.button("Submit"):
    if uploaded_file is None:
        st.info("Please upload a CSV file.")
    elif not user_abstract:
        st.info("Please enter your paper's Abstract.")
    else:
        # Read CSV file
        df = pd.read_csv(uploaded_file)

        # Extract only necessary columns
        required_columns = ['Publication Year', 'Title', 'Author', 'Abstract Note']
        df_filtered = df[required_columns].dropna()

        # Sort by Publication Year
        df_sorted = df_filtered.sort_values('Publication Year')

        # Convert to JSON format
        literature_review = []
        for _, row in df_sorted.iterrows():
            paper = {
                'Publication_Year': str(row['Publication Year']),
                'Title': row['Title'],
                'Author': row['Author'],
                'Abstract_Note': row['Abstract Note']
            }
            literature_review.append(paper)

        json_string = json.dumps(literature_review, ensure_ascii=False, indent=2)

        # Use OpenAI API to organize by themes
        prompt = f"""Here is the user's paper Abstract:

{user_abstract}

Please analyze the following JSON-formatted literature information and organize it by main themes considering its relevance to the user's paper. Output in Markdown format. List related papers under each theme in the following format:

## Theme
#### {{Paper Title}}
- Paper Summary: {{Paper summary}}
- Relevance: {{Explanation of how it relates to the user's paper}}

#### {{Paper Title}}
- Paper Summary: {{Paper summary}}
- Relevance: {{Explanation of how it relates to the user's paper}}

## Theme 2
- ...

JSON literature information:

{json_string}"""
        
        # Display OpenAI input
        input_display = st.empty()
        input_display.text_area("OpenAI API Input:", value=prompt, height=300)
        
        # Loading indicator
        with st.spinner('Organizing Related Work through OpenAI API. Please wait...'):
            # Create empty container for streaming output
            output_container = st.empty()
            full_response = ""
            
            # Generate streaming response
            for chunk in client.chat.completions.create(
                model="chatgpt-4o-latest",
                messages=[
                    {"role": "system", "content": "You are an expert in organizing literature reviews."},
                    {"role": "user", "content": prompt}
                ],
                stream=True,
            ):
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    output_container.markdown(full_response)
            
            # Display final response
            output_container.markdown(full_response)
        
        # Display data preview
        st.subheader("Uploaded Data Preview")
        st.dataframe(df_sorted)
        
        # Display basic data information
        st.subheader("Basic Data Information")
        st.write(f"Total number of papers: {len(df_sorted)}")
        st.write(f"Year range: {df_sorted['Publication Year'].min()} - {df_sorted['Publication Year'].max()}")