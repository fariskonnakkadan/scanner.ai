import sys
import subprocess
import markdown
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QLineEdit

# Replace with your actual OpenAI API setup
class OpenAI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key

    def chat(self, model, messages, temperature):
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        response = requests.post(url, headers=headers, json=data)
        return response.json()

class Worker(QThread):
    status_update = pyqtSignal(str)
    response_update = pyqtSignal(str)
    analysis_update = pyqtSignal(str)
    error_update = pyqtSignal(str)

    def __init__(self, curl_command, openai_client):
        super().__init__()
        self.curl_command = curl_command
        self.openai_client = openai_client

    def run(self):
        try:
            # Emit status update
            self.status_update.emit("Executing cURL request...")

            # Execute cURL request
            result = subprocess.run(self.curl_command, shell=True, capture_output=True, text=True, check=True)
            
            # Emit response update
            response_text = result.stdout
            self.response_update.emit(response_text)
            
            # Emit status update
            self.status_update.emit("cURL request executed. Fetching response...")
            
            # Prepare the request and response for OpenAI
            messages = [
                {"role": "system", "content": "Analyse request and response and give a custom tailored checklist for penetration testing this specific endpoint."},
                {"role": "user", "content": f"Request: {self.curl_command}\n\nResponse: {response_text}"}
            ]

            # Emit status update
            self.status_update.emit("Sending data to OpenAI API...")

            # Get response from OpenAI
            openai_response = self.openai_client.chat(
                model="lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF",
                messages=messages,
                temperature=0.7
            )

            # Emit analysis update
            openai_message = openai_response['choices'][0]['message']['content']
            self.analysis_update.emit(openai_message)

            # Final status update
            self.status_update.emit("Analysis complete.")

        except subprocess.CalledProcessError as e:
            self.error_update.emit(f"Error executing cURL command: {e}")
            self.status_update.emit("Error during cURL execution.")
        except requests.RequestException as e:
            self.error_update.emit(f"Error with OpenAI API request: {e}")
            self.status_update.emit("Error during OpenAI API request.")
        except Exception as e:
            self.error_update.emit(f"An unexpected error occurred: {e}")
            self.status_update.emit("An unexpected error occurred.")

class MyApp(QWidget):
    def __init__(self):
        super().__init__()

        # Initialize the layout
        main_layout = QVBoxLayout()
        upper_layout = QHBoxLayout()
        
        # Create labels and text boxes
        self.label1 = QLabel('Request:', self)
        self.textbox1 = QTextEdit(self)  # For cURL request
        
        self.label2 = QLabel('Response:', self)
        self.textbox2 = QTextEdit(self)  # For cURL response
        
        self.label4 = QLabel('Status:', self)
        self.textbox4 = QLineEdit(self)  # For status
        self.textbox4.setReadOnly(True)  # Make the status text box read-only

        self.label3 = QLabel('Analysis:', self)
        self.textbox3 = QTextEdit(self)  # For OpenAI response
        self.textbox3.setReadOnly(True)  # Make the analysis text box read-only

        # Create vertical layouts for each section
        upper_left_layout = QVBoxLayout()
        upper_left_layout.addWidget(self.label1)
        upper_left_layout.addWidget(self.textbox1)
        
        upper_right_layout = QVBoxLayout()
        upper_right_layout.addWidget(self.label2)
        upper_right_layout.addWidget(self.textbox2)

        # Add vertical layouts to the upper horizontal layout
        upper_layout.addLayout(upper_left_layout)
        upper_layout.addLayout(upper_right_layout)

        # Create button
        self.button = QPushButton('Execute and Analyze', self)

        # Add layouts and button to the main layout
        main_layout.addLayout(upper_layout)
        main_layout.addWidget(self.label4)
        main_layout.addWidget(self.textbox4)
        main_layout.addWidget(self.label3)
        main_layout.addWidget(self.textbox3)
        main_layout.addWidget(self.button)

        # Set layout to the window
        self.setLayout(main_layout)

        # Set window properties
        self.setWindowTitle('PyQt5 Layout Example')
        self.setGeometry(100, 100, 600, 400)

        # Connect button click to the handler
        self.button.clicked.connect(self.start_worker)

        # Initialize OpenAI client
        self.openai_client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

    def start_worker(self):
        curl_command = self.textbox1.toPlainText()
        self.worker = Worker(curl_command, self.openai_client)
        self.worker.status_update.connect(self.update_status)
        self.worker.response_update.connect(self.update_textbox2)
        self.worker.analysis_update.connect(self.update_textbox3)
        self.worker.error_update.connect(self.update_textbox3)
        self.worker.start()

    def update_status(self, message):
        self.textbox4.setText(message)

    def update_textbox2(self, message):
        self.textbox2.setPlainText(message)

    def update_textbox3(self, message):
        # Convert Markdown to HTML and set the text in textbox3
        html = markdown.markdown(message)
        self.textbox3.setHtml(html)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
