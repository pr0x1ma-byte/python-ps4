# PS4-iot

Integrate your PS4 as an IOT device with your Google Home. 

# Overview

The python-ps4 project allows you to control your playstation with your voice with Google!

# Build Instructions

## Prerequisites

- Python 3.6+
- [Node.js](https://nodejs.org/) LTS 10.16.0+
- [Firebase CLI](https://firebase.google.com/docs/cli)

## Configure the Actions project

> Note: This project uses
> [Cloud Functions for Firebase](https://firebase.google.com/docs/functions),
> which requires you to associate a billing account with your project.
> Actions projects do not create a billing account by default. See
> [Create a new billing account](https://cloud.google.com/billing/docs/how-to/manage-billing-account#create_a_new_billing_account)
> for more information.

- Create a new _Smart Home_ project in the [Actions console](https://console.actions.google.com/)
- Deploy the placeholder smart home provider to _Cloud Functions for Firebase_
  using the same Project ID:
  ```
  npm install --prefix functions/
  npm run firebase --prefix functions/ -- use ${PROJECT_ID}
  npm run deploy --prefix functions/
  ```
- In _Develop > Actions_, set the following configuration values that matches the
  _Cloud Functions for Firebase_ deployment:
  - **Fulfillment**: `https://${REGION}-${PROJECT_ID}.cloudfunctions.net/smarthome`
- In _Develop > Account linking_, set the following configuration values:
  - **Linking type**: `OAuth` / `Authorization code`
  - **Client ID**:: `placeholder-client-id`
  - **Client secret**: `placeholder-client-secret`
  - **Authorization URL**: `https://${REGION}-${PROJECT_ID}.cloudfunctions.net/authorize`
  - **Token URL**: `https://${REGION}-${PROJECT_ID}.cloudfunctions.net/token`

### Select a discovery protocol

Choose one of the supported the discovery protocols that you would like to test,
and enter its attributes in the Actions console at
_Develop > Actions > Configure local home SDK_ under **Device Scan Configuration**.

> Note: These are the default values used by the [virtual device](device/README.md)
> for discovery. If you choose to use different values, you will need to supply
> those parameters when you [set up the virtual device](#set-up-the-virtual-device).

#### UDP
- **Broadcast address**: `255.255.255.255`
- **Broadcast port**: `3312`
- **Listen port**: `3311`
- **Discovery packet**: `A5A5A5A5`

## Deploy the local execution app

Serve the sample app locally from the same local network as the Home device,
or deploy it to a publicly reacheable URL endpoint.

- Start the local development server:
  ```
  npm install --prefix app/
  npm run build --prefix app/
  npm start --prefix app/
  ```
  > Note: The local development server needs to listen on the same local network as
  > the Home device in order to be able to load the Local Home SDK application.

- Go to the smart home project in the [Actions console](https://console.actions.google.com/)
- In _Develop > Actions > On device testing_ set the **Chrome** and **Node** development URLs to the ones displayed in the local development server logs.

### Deploy Playstation App
Configure `ip`, `port`, and `credential` in ` python-ps4.ini` located in your ${HOME} directory. 

- **IP**: The address where python app is hosted
- **Port**: The port the python web app is served on
- **Credential**: The credential is obtained from the playstation using the playstation second screen app and Wireshark (need to automate this setup)
To build the python application run:
    `make run`