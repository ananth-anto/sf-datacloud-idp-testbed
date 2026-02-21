# Salesforce Data Cloud - Document AI API Testbed

## Introduction

This project provides a sample implementation demonstrating how to use the Salesforce Data Cloud Document AI APIs. It creates a simple web interface that allows users to upload documents (PDFs or images) along with a JSON schema, and then processes these documents using Salesforce's document extraction capabilities.

The application showcases how to:
- Make authenticated API calls to Salesforce Data Cloud Document AI endpoints using OAuth 2.0
- Process document uploads and convert them to base64 encoding
- Submit documents for intelligent extraction with custom schema configurations
- Display the extracted structured data from documents
- Use confidence scores to assess extraction accuracy and identify fields needing review

This testbed serves as a reference implementation for developers looking to integrate Salesforce Data Cloud's document processing capabilities into their own applications.

Youtube video walkthrough: https://youtu.be/H8cgvUP7Ytg

## Features

- **OAuth 2.0 Authentication**: Secure authentication flow with Salesforce using PKCE
- **Multiple ML Models**: Choose between Gemini Fast and OpenAI GPT-4o
- **Confidence Scores**: Optional accuracy scores (0–1) per extracted field with color-coded badges; see [release notes](https://help.salesforce.com/s/articleView?id=release-notes.rn_cdp_2026_spring_confidence_score_document_ai.htm&release=260&type=5)
- **Page Range Selection**: Extract from specific PDF pages (e.g. 1–5); see [release notes](https://help.salesforce.com/s/articleView?id=release-notes.rn_cdp_2026_spring_page_start_end_document_ai.htm&release=260&type=5)
- **Schema-Level Prompt**: Global extraction instructions sent as the schema root-level `description`; see [release notes](https://help.salesforce.com/s/articleView?id=release-notes.rn_cdp_2026_spring_config_prompt_document_ai.htm&release=260&type=5)
- **Custom JSON Schemas**: Define your own extraction schemas for any document type
- **Formatted / Raw JSON**: Toggle between tree view (with optional confidence badges) and raw JSON for every result
- **Developer Reference**: After each successful extraction, copy the exact **curl** and **Apex** request (collapsible section)
- **Multiple File Formats**: Support for PDF, PNG, JPG, JPEG, TIFF, and BMP
- **JSON Schema Generator**: Built-in tool to help create extraction schemas
- **Real-time Processing**: Instant document analysis with visual feedback

## Project Structure

```
sf-datacloud-idp-testbed/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings (API URLs, OAuth settings)
├── api_client.py          # API client for token management
├── requirements.txt       # Python dependencies
├── static/                # Static assets
│   ├── css/               # CSS stylesheets
│   │   └── style.css      # Main stylesheet
│   ├── js/                # JavaScript files
│   │   └── script.js      # Client-side functionality
│   └── json-jazz.html     # JSON Schema Generator tool
├── templates/             # HTML templates
│   └── index.html         # Main interface page
├── .env.example           # Example environment file
├── README.md              # Project documentation
└── UPDATE_POST.md         # Release summary and feature links for sharing
```

## Environment Setup

> **⚠️ IMPORTANT:** You MUST create a `.env` file with your Salesforce credentials before running the application. Without this file, you will see a "Salesforce configuration missing on server" error.

1. **Clone the Repository**
    ```bash
    git clone https://github.com/ananth-anto/sf-datacloud-idp-testbed
    cd sf-datacloud-idp-testbed
    ```

2. **Create Environment File (REQUIRED)**
    
    Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
    
    **This step is mandatory!** The application will not work without a `.env` file.

3. **Configure Salesforce Connected App**
    - Follow the [Setting Up External Client App guide](https://help.salesforce.com/s/articleView?id=sf.remoteaccess_authenticate.htm&type=5)
    - **Important:** Use callback URL as `http://localhost:3000/auth/callback`
    - Open the `.env` file you just created and replace the placeholder values with your actual Salesforce credentials

    Your `.env` file should look like this (with your actual values):
    ```env
    LOGIN_URL=your-actual-salesforce-login-url.my.salesforce.com
    CLIENT_ID=your-actual-connected-app-client-id
    CLIENT_SECRET=your-actual-connected-app-client-secret
    API_VERSION=v65.0
    TOKEN_FILE=access-token.secret
    ```
    
    **Note:** 
    - Replace `your-actual-salesforce-login-url` with your Salesforce domain (e.g., `login.salesforce.com` or your custom domain)
    - Replace `CLIENT_ID` and `CLIENT_SECRET` with values from your Connected App
    - Use `API_VERSION=v65.0` for the Document AI extract-data endpoint (v66 may return 404 on some instances)

4. **Create a Virtual Environment (Recommended)**
    ```bash
    python -m venv venv
    ```
    - On macOS/Linux:
      ```bash
      source venv/bin/activate
      ```
    - On Windows:
      ```bash
      venv\Scripts\activate
      ```

5. **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

6. **Run the Application**
    ```bash
    python app.py
    ```
    - The application will start and be available at `http://localhost:3000/` in your web browser.

---

## Using the Application

### Authentication Flow (OAuth 2.0 Web Server Flow)

1. **First Time Setup**: When you first visit the application, you'll see an "Authenticate with Salesforce" button
2. **Click Authenticate**: This will redirect you to Salesforce login page
3. **Login**: Enter your Salesforce credentials
4. **Authorize**: Grant permissions to the connected app
5. **Return**: You'll be redirected back to the application with a code in the URL
6. **Token Exchange**: The backend exchanges the code for an access token and instance URL
7. **Ready to Use**: The "Analyze Document" button will now be enabled

### Document Processing

1. Upload a document (supported formats: PDF, PNG, JPG, JPEG, TIFF, BMP)
2. Select an ML Model (Gemini Fast or OpenAI GPT-4o)
3. **Optional**: Enable "Include Confidence Scores" to get accuracy scores (0–1) for each extracted field
4. **Optional**: Enter a Schema-Level Prompt (global instructions; sent as the schema root `description`)
5. Enter a JSON schema defining the data structure you want to extract
6. Click "Analyze Document" to process the document
7. View results: switch between **Formatted** (tree view) and **Raw JSON**, and expand **Show API request** to copy the curl or Apex snippet

### Confidence Scores Feature

When enabled, the confidence score feature provides an accuracy score (0-1) for each extracted field, helping you identify which values may need manual review:

- **Green (≥0.8)**: High confidence - extracted value is highly accurate
- **Yellow (0.5-0.79)**: Medium confidence - may need verification
- **Red (<0.5)**: Low confidence - should be manually reviewed

The color-coded display makes it easy to quickly identify fields that require attention, optimizing your review process and maintaining high-quality data.

### Page Range Selection (PDF Only)

For multi-page PDF documents, you can specify which pages to process:

1. Upload a PDF file
2. Enter the total number of pages in the document
3. Optionally specify a page range (e.g., "1-5" or "3-10")
4. Leave range blank to process all pages

**Benefits:**
- Process only relevant pages from large documents
- Reduce processing time and costs
- Improve extraction accuracy by focusing on specific sections
- Handle documents that exceed size guardrails by processing in chunks

**Example use cases:**
- Extract data only from the first page of a multi-page contract
- Process pages 5-10 of a 50-page financial report
- Skip cover pages and process only content pages

## JSON Schema Format

The schema should be formatted as a JSON object that defines the fields you want to extract from the document. The optional **Schema-Level Prompt** in the UI is passed as the schema's root-level `description` for extraction instructions, per the [Document AI API spec](https://developer.salesforce.com/docs/data/connectapi/references/spec?meta=extractDocumentAIConfigData). For example:

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

## Authentication

The application uses OAuth 2.0 Web Server Flow (Authorization Code Grant) for authentication with Salesforce Data Cloud. The authentication flow:

1. **User clicks "Authenticate" button** - Frontend calls `/api/auth-info` to get Salesforce configuration
2. **User logs into Salesforce** - User enters credentials on Salesforce login page
3. **Salesforce redirects back** - With a code in the URL
4. **Token is exchanged and saved** - Backend exchanges the code for an access token and instance URL, which are stored in `access-token.secret`
5. **Token is used for API calls** - All subsequent API calls use the stored token and instance URL

### Token Management

- **Storage**: Access tokens and instance URLs are stored locally in `access-token.secret`
- **Security**: The token file is automatically added to `.gitignore` to prevent accidental commits
- **Expiration**: Salesforce access tokens expire. When expired, users will need to re-authenticate
- **Validation**: The application checks authentication status before allowing document processing

## Troubleshooting

### Common Issues

1. **"Salesforce configuration missing on server" Error**: This is the most common issue during initial setup.
   - **Cause**: The `.env` file does not exist or is not properly configured
   - **Solution**: 
     - Ensure you've created a `.env` file by running `cp .env.example .env`
     - Open the `.env` file and replace all placeholder values with your actual Salesforce credentials
     - Restart the Flask application after creating/updating the `.env` file
     - Verify the `.env` file is in the root directory of the project (same folder as `app.py`)

2. **Authentication Errors (401/403)**: If you receive a 401 or 403 error after initial setup, your access token may be expired. 
   - Click the "Authenticate with Salesforce" button to get a new token
   
3. **Connected App Configuration**: Ensure your Salesforce Connected App has the correct callback URL and OAuth scopes configured.
   - Callback URL must be exactly: `http://localhost:3000/auth/callback`
   - Required OAuth scopes: Full access (full), Perform requests at any time (refresh_token, offline_access)

4. **Document AI endpoint not found (404)**: The request to the document-processing API returns 404 (even when Document AI is enabled).
   - **Cause**: The API path can differ by instance or API version. Document AI may also not be provisioned on some orgs (e.g. Trailhead).
   - **Solution**:
     - The app automatically retries with path `ssot/document-processing/extract-data` (without `actions`) on 404. If that still fails, set in `.env`: `DOCUMENT_AI_EXTRACT_PATH=ssot/document-processing/extract-data` and restart.
     - Try a different API version in `.env`: `API_VERSION=v65.0` or `API_VERSION=v64.0`.
     - Confirm Document AI is enabled: Setup → Data Cloud / Data 360 → Document AI.
     - Check the [Data 360 Connect API](https://developer.salesforce.com/docs/data/connectapi/overview) or Postman collection for the current extract endpoint path.

5. **Schema Errors**: Ensure your schema is valid JSON and follows the expected format for the Salesforce Data Cloud Document AI API.

6. **File Format Issues**: Check that your document is in one of the supported formats and is not corrupted.
   - Supported formats: PDF, PNG, JPG, JPEG, TIFF, BMP

### Debugging

The application has logging enabled. Check the console output for detailed error messages and debugging information.

## Security Considerations

This testbed is intended for development and testing purposes only. For production use:

1. Never hardcode authentication tokens in your code
2. Implement proper user authentication and authorization
3. Use HTTPS in production for secure token transmission
4. Consider implementing token refresh logic for long-running applications
5. Store tokens in secure, encrypted storage rather than local files

## API Endpoints

- `GET /` - Main application interface
- `GET /api/status` - Check authentication status
- `GET /api/auth-info` - Get OAuth configuration
- `GET /auth/callback` - OAuth callback page (handles code exchange)
- `POST /extract-data` - Process document extraction
  - Parameters:
    - `file` (required): Document file (PDF or image)
    - `schema` (required): JSON schema for extraction
    - `config_prompt` (optional): Schema-level instructions (sent as schema root `description`)
    - `ml_model` (optional): ML model to use
    - `include_confidence` (optional): Include confidence scores (true/false)
    - `page_range` (optional): Page range for PDFs (format: "startPage-endPage", e.g., "1-5")
  - Returns: Extracted data (and optional metadata/confidence); response shape is `{ data, metadata?, apiRequest? }`

## Documentation and release notes

- **API reference**: [Extract Document AI Config Data](https://developer.salesforce.com/docs/data/connectapi/references/spec?meta=extractDocumentAIConfigData) (Data 360 Connect API)
- **Config prompt (schema-level instructions)**: [Release notes](https://help.salesforce.com/s/articleView?id=release-notes.rn_cdp_2026_spring_config_prompt_document_ai.htm&release=260&type=5)
- **Confidence scores**: [Release notes](https://help.salesforce.com/s/articleView?id=release-notes.rn_cdp_2026_spring_confidence_score_document_ai.htm&release=260&type=5)
- **Page start/end**: [Release notes](https://help.salesforce.com/s/articleView?id=release-notes.rn_cdp_2026_spring_page_start_end_document_ai.htm&release=260&type=5)

## Dependencies

- Flask==3.0.2
- Werkzeug==3.0.1
- requests==2.31.0

## License

This project is licensed under the MIT License - see the LICENSE file for details.
