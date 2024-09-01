# MIDAS (California Energy Prices)

Custom integration to get the current electricity price and other data for many California electric bills from the California energy regulator's electricity price API MIDAS.

If your electric bill has a **RIN QR Code** on it, you can use this integration to get your current electricity price.

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=MattDahEpic&repository=ha-midas)

To install this integration, add this GitHub Repo to the HACS Custom Repositories, or click the badge above.

## Configuration

Configuration is done in the UI, please follow the steps below for guidance.

1. Add the integration in the `Devices & services` section or click this add link:
[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=midas)
2. Choose whether you have a MIDAS account or not.
  ![Config step 1: Do you have a MIDAS account? Yes or no](.pictures/config-step1.png)
3. If you don't have a MIDAS account the integration will help you create one.
  ![Config step 1.5: Create a MIDAS account.](.pictures/config-step1.5.png)
  Once complete, click the link sent to your email to activate your account.
  ![Config step 1.75: MIDAS account creation successful. Please click the link in your email to activate the account before continuing.](.pictures/config-step1.75.png)
4. Enter your MIDAS account information.
  ![Config step 2: Enter your MIDAS account credentials](.pictures/config-step2.png)
5. Enter one or more Rate IDs to monitor, obtained from the QR code on your electric bill.
  ![Config step 3: Enter Rate IDs to monitor](.pictures/config-step3.png)
6. A device will be created for each Rate ID entered.
  ![Config step 4: Devices are created for each entered RID](.pictures/config-step4.png)

These entities can be used in the Energy dashboard to set prices, in automations to help conserve energy when prices will increase soon, and more!
![Price entities being used in the Energy dashboard for price tracking](.pictures/energy-dashboard-usage.png)

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)
