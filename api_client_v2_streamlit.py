"""
Client for API v2
"""

import json
import requests
import streamlit as st

from utils import get_console_logger

TIMEOUT = 240
API_URL = "http://localhost:8888"
# API_URL = "https://cnqvldwtqizheroelszndsocdy.apigateway.us-chicago-1.oci.customer-oci.com/text2sql"

# Define the available operations
operations = {"handle_request_v2": "/v2/handle_data_request"}

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


def main():
    """
    main
    """
    st.title("FastAPI Client with Streamlit")

    # Select operation
    selected_operation = st.selectbox(
        "Select an API Operation", list(operations.keys())
    )

    if selected_operation in ["handle_request_v2"]:
        st.subheader("Input data")
        conv_id = st.text_input("Conversation ID")
        user_query = st.text_area("User Query")

        # Create a dictionary for the request body
        request_body = {"conv_id": conv_id, "user_query": user_query}

    # API call
    if st.button("Send Request"):
        # Make the API request to the selected operation
        endpoint = API_URL + operations[selected_operation]

        # here we call the api
        response = requests.post(endpoint, json=request_body, timeout=TIMEOUT)

        # Display the response
        if response.status_code == 200:
            st.success("Success!")

            # If the response is not JSON (like binary/text), convert it to a JSON-like structure
            try:
                json_response = response.json()  # Try to parse JSON directly
            except Exception:
                # If response is not JSON, convert binary/text to JSON manually
                json_response = convert_to_json(response.content)

            if json_response:
                logger.info("")
                logger.info(json_response)
                logger.info("")

                if json_response["type"] == "data":
                    # display a table with the data
                    st.table(json_response["content"])
                else:
                    # display a report
                    st.write(json_response["content"])

    # Run the app


if __name__ == "__main__":
    main()
