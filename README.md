# Salesforce Data Cloud - IDP API Testbed

## Introduction

This project provides a sample implementation demonstrating how to use the Salesforce Data Cloud Intelligent Document Processing (IDP) APIs. It creates a simple web interface that allows users to upload documents (PDFs or images) along with a JSON schema, and then processes these documents using Salesforce's document extraction capabilities.

The application showcases how to:
- Make authenticated API calls to Salesforce Data Cloud IDP endpoints
- Process document uploads and convert them to base64 encoding
- Submit documents for intelligent extraction with custom schema configurations
- Display the extracted structured data from documents

This testbed serves as a reference implementation for developers looking to integrate Salesforce Data Cloud's document processing capabilities into their own applications.

## Project Structure

```
sf-datacloud-idp-testbed/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings (API URLs, tokens)
├── requirements.txt       # Python dependencies
├── static/                # Static assets
│   ├── css/               # CSS stylesheets
│   │   └── style.css      # Main stylesheet
│   └── js/                # JavaScript files
│       └── script.js      # Client-side functionality
└── templates/             # HTML templates
    └── index.html         # Main interface page
```

## Prerequisites

- Python 3.8 or higher
- Access to Salesforce Data Cloud with appropriate permissions
- Valid Salesforce API authentication token

## Installation and Local Deployment

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/sf-datacloud-idp-testbed.git
cd sf-datacloud-idp-testbed
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
```

#### Activate the virtual environment:

On macOS/Linux:
```bash
source venv/bin/activate
```

On Windows:
```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Application

Before running the application, you need to update the `config.py` file with your Salesforce Data Cloud credentials:

```python
# Salesforce API configuration
SF_API_URL = "https://your-instance.my.salesforce.com/services/data/v63.0/ssot/document-processing/actions/extract-data"
SF_API_TOKEN = "your-bearer-token"

# Default model configuration
DEFAULT_ML_MODEL = "llmgateway__OpenAIGPT4Omni_08_06"  # Or your preferred model
```

Key items to update:
- `SF_API_URL`: Replace with your Salesforce Data Cloud instance URL
- `SF_API_TOKEN`: Replace with your valid Salesforce authentication token
- `DEFAULT_ML_MODEL`: Optionally update if using a different model

### 5. Run the Application

```bash
python app.py
```

The application will start and be available at `http://127.0.0.1:5000` in your web browser.

## Using the Application

1. Open your browser and navigate to `http://127.0.0.1:5000`
2. Upload a document (supported formats: PDF, PNG, JPG, JPEG, TIFF, BMP)
3. Enter a JSON schema defining the data structure you want to extract
4. Click "Analyze Document" to process the document
5. View the extracted structured data in the results section

## JSON Schema Format

The schema should be formatted as a JSON object that defines the fields you want to extract from the document. For example:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "VendorName": {
      "type": "string",
      "description": "Name of the vendor issuing the invoice"
    },
    "Vendor Address": {
      "type": "string",
      "description": "Full address of the vendor"
    },
    "Vendor Phone number": {
      "type": "string",
      "description": "Phone number"
    },
    "Billing Address": {
      "type": "string",
      "description": "Full name and address of the billing entity"
    },
    "Product Item List": {
      "type": "array",
      "items": {
        "type": "object",
        "description": "Table containing the list of products",
        "properties": {
          "Item ID": {
            "type": "string",
            "description": "Item id"
          },
          "Item Description": {
            "type": "string",
            "description": "Full description for the item"
          },
          "Quantity": {
            "type": "number",
            "description": "Number of items"
          },
          "Unit Price": {
            "type": "number"
          },
          "Line total": {
            "type": "number",
            "description": "Line total for the product line item"
          }
        }
      },
      "description": "Table containing the list of products"
    },
    "Total amount": {
      "type": "number"
    }
  }
}
```
When passing the schema to the API, make sure to pass it without new line characters like how it is shown below:

{ "$schema": "http://json-schema.org/draft-07/schema#", "type": "object", "properties": { "VendorName": { "type": "string", "description": "Name of the vendor issuing the invoice" }, "Vendor Address": { "type": "string", "description": "Full address of the vendor" }, "Vendor Phone number": { "type": "string", "description": "Phone number" }, "Billing Address": { "type": "string", "description": "Full name and address of the billing entity" }, "Product Item List": { "type": "array", "items": { "type": "object", "description": "Table containing the list of products", "properties": { "Item ID": { "type": "string", "description": "Item id" }, "Item Description": { "type": "string", "description": "Full description for the item" }, "Quantity": { "type": "number", "description": "Number of items" }, "Unit Price": { "type": "number" }, "Line total": { "type": "number", "description": "Line total for the product line item" } } }, "description": "Table containing the list of products" }, "Total amount": { "type": "number" } }}

You can use the json-jazz.html file to open locally to create the above schema using UI. Once you have created the structured needed, you can click on "Copy for API" button on the right which will copy the json in a format amenable to APIs. Use this to pass as param to the IDP APIs.

## Authentication

The application uses a bearer token for authentication with Salesforce Data Cloud. This token needs to be:
- Valid and not expired
- Associated with a user that has appropriate permissions
- Updated in the `config.py` file when it expires

## Troubleshooting

### Common Issues

1. **Authentication Errors**: If you receive a 401 or 403 error, your bearer token may be expired or invalid.
   
2. **Schema Errors**: Ensure your schema is valid JSON and follows the expected format for the Salesforce Data Cloud IDP API.

3. **File Format Issues**: Check that your document is in one of the supported formats and is not corrupted.

### Debugging

The application has logging enabled. Check the console output for detailed error messages and debugging information.

## Security Considerations

This testbed is intended for development and testing purposes only. For production use:

1. Never hardcode authentication tokens in your code
2. Implement proper user authentication and authorization
3. Use environment variables or a secure secrets management solution
4. Add proper error handling and validation
5. Consider rate limiting and other security measures


## License

This project is licensed under the MIT License - see the LICENSE file for details.
