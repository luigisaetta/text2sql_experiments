"""
Streamlit API client
"""

import json
import requests
import streamlit as st

from utils import get_console_logger

API_URL = "http://localhost:8888"

# Define the available operations
operations = {
    "Generate SQL": "/generate/",
    "Generate and Execute SQL": "/generate_and_exec_sql/",
    "Explain AI Response": "/explain_ai_response/",
}

logger = get_console_logger()


def convert_to_json(response_content):
    """
    to convert to json if the output is not json
    """
    try:
        # Try decoding binary response if it's not already a string
        if isinstance(response_content, bytes):
            decoded_content = response_content.decode("utf-8")
        else:
            decoded_content = str(response_content)

        # Clean up escaped newlines (\\n -> \n) and other escape sequences
        cleaned_content = decoded_content.encode("utf-8").decode("unicode_escape")

        # Convert the decoded string into a JSON structure with a key
        return json.dumps({"generated_sql": cleaned_content}, indent=2)
    except Exception as e:
        st.error(f"Error converting response to JSON: {e}")
        return None


# Define the main Streamlit app
def main():
    """
    main
    """
    st.title("FastAPI Client with Streamlit")

    # Select operation
    selected_operation = st.selectbox(
        "Select an API Operation", list(operations.keys())
    )

    # Input fields based on the selected operation
    if selected_operation in ["Generate SQL", "Generate and Execute SQL"]:
        st.subheader("Input data")
        conv_id = st.text_input("Conversation ID")
        user_query = st.text_area("User Query")

        # Create a dictionary for the request body
        request_body = {"conv_id": conv_id, "user_query": user_query}

    elif selected_operation == "Explain AI Response":
        st.subheader("Input data")
        conv_id = st.text_input("Conversation ID")
        user_query = st.text_area("User Query")
        rows = st.text_area("Rows (comma-separated values for each row)")

        # Convert rows input to a list
        rows_list = [row.strip() for row in rows.split(",") if row.strip()]

        # Create a dictionary for the request body
        request_body = {"conv_id": conv_id, "user_query": user_query, "rows": rows_list}

    # Button to trigger the API call
    if st.button("Send Request"):
        # Make the API request to the selected operation
        endpoint = API_URL + operations[selected_operation]

        # here we call the api
        response = requests.post(endpoint, json=request_body, timeout=30)

        # Display the response
        if response.status_code == 200:
            st.success("Success!")

            # If the response is not JSON (like binary/text), convert it to a JSON-like structure
            try:
                response_json = response.json()  # Try to parse JSON directly
                st.json(response_json)
            except Exception:
                # If response is not JSON, convert binary/text to JSON manually
                json_response = convert_to_json(response.content)

                if json_response:
                    st.json(json.loads(json_response))

        else:
            st.error(f"Error: {response.status_code}")
            st.json(response.json())


# Run the app
if __name__ == "__main__":
    main()
