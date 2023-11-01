# NOWPayments API

[![Black](https://github.com/Ventura94/NOWPayments-Python-API/actions/workflows/black.yml/badge.svg)](https://github.com/tomazmm/nowpayments-api-python/actions/workflows/black.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
 
A Python wrapper for the [NOWPayments API](https://documenter.getpostman.com/view/7907941/2s93JusNJt), allowing easy integration with the NowPayments platform in Python applications.
The api call descriptions are from the official documentation.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Project Status](#project-status)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)


## Installation
Make sure you have Python and `pip` installed. Install by running:
```bash
pip install <insert-package-name>
```

## Usage
1. Obtain your NowPayments API key.
   1. From [NowPayments Dashboard](https://account.nowpayments.io/dashboard) or
   2. From [NowPayments Sandbox Dashboard](https://account-sandbox.nowpayments.io/dashboard)

2. Create an instance of the NowPaymentsAPI class based on your API key:

```python
# Production
from nowpayments_api import NOWPaymentsAPI

api_key = 'YOUR_API_KEY'
nowpayments = NOWPaymentsAPI(api_key)
status = nowpayments.get_api_status()
```

```python
# Sandbox
from nowpayments_api import NOWPaymentsAPI

api_key = 'YOUR_SANDBOX_API_KEY'
nowpayments = NOWPaymentsAPI(api_key, sandbox=True)
status = nowpayments.get_api_status()
```

## Project Status
This project is under active development. Below are the implemented API methods

### Auth and API Status
- [x] GET API Status
- [x] POST Auth

### Currencies
- [x] GET Available Currencies
- [x] GET Available Currencies Full / Detailed 
- [x] GET Available Currencies Checked

### Payments
- [x] POST Create invoice
- [x] POST Create payment
- [x] POST Create payment by invoice
- [ ] POST Update payment estimate
- [x] GET Estimate price
- [x] GET Payment Status
- [x] GET List of payments
- [x] GET Minimum payment amount

### Mass Payout
TBA

### Conversions
TBA

### Custody
TBA

## Documentation
For more details on available API methods and parameters, refer to the NowPayments API Documentation.

## Contributing
Contributions are welcome! <br> If you find any issues or have suggestions for improvements, please open an issue or create a pull request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.


