# CSI Chatbot

## How to Run?
1. Clone the repository
2. Install the dependencies 
    ```
    pip install -r requirements.txt
    ```
3. Start the flask server
    ```
    flask --app app run
    ```
3. The flask server starts at [localhost's port 5000](http://127.0.0.1:5000).
4. Now using any Web Application (or HTTP clients like POSTMAN), you can start sending POST requests to the route `/chatservice`, to get the answer to your question.

    Sample request body -
    ```
    {
        "question": "<Your Question Goes in Here!>"
    }
    ```

    Or you can also use curl to make requests -
    ```
    curl --location 'http://127.0.0.1:5000/chatservice' \
        --header 'Content-Type: application/json' \
        --data '{
            "question": "<Your Question Goes in Here!>"
        }'
    ```