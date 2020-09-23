# IDMA Developer Onboarding

This describes the process for developers to get access to the XBR network and IDMA test data markets.


## Overview

All sharing of data for the IDMA happens in the IDMA Test Data Markets that we have set up.

The XBR Network provides the cross-market identity for participants and this allows you to join individual data markets.

This document describes:

- pre-requisites for joining the XBR network
- the process for joining the XBR network using our browser-based GUI
- the process for joining any IDMA test data market using our browser-based GUI

Runing a first demo application within a test data market, so that you can start your development with working code, is covered in a separate document.


## Pre-Requisites

All major interactions with the XBR network and a data market (including the initial request for registration in the XBR network) require signing from an Ethereum wallet. Ownership of the private wallet key is the proof of identity here.

For the browser-based flows we are currently using the MetaMask browser extension, which works in either Chrome or Firefox.

To set up MetaMask, follow [these instructions](https://github.com/crossbario/idma-examples/blob/master/gettingstarted/onboarding/installing_metamask.md).

Once you have installed this and created or imported a wallet you want to use for your interactions with the XBR network, you can proceed to the next step.


## Registering with the XBR Network

To start registration with the XBR Network, go to

[https://planet.xbr.network/register](https://planet.xbr.network/register)

For registration with the XBR Network you need to provide a valid eamil address, a username and the address of the wallet you want to use for participation in the XBR Network. 

You also need to allow the site to connect to the MetaMask installed in your browser. To so just press "CONNECT" in the MetaMask confirmation window that pops up. 

Note: All you are granting here is for our site make further requests to MetaMask. You retain full control over each further step that requires signing by MetaMask and will need to sign each further request (e.g. for joining the XBR Network) individually. All further signatures with MetaMask are also only for that specific request or action. If you want to feel extra-safe then we suggest creating an account in MetaMask which you only use for the IDMA.


### Email

You will need access to the email address for registration verification as well as for login (we use passwordless login).


### Username

The username needs to be globally unique within the XBR Network. Requirements for the name are:

- between 4 and 14 characters
- starts with an alphabet character
- may contain alphanumerics and underscore

Note: In case you choose a username that is already taken you will receive feedback after submitting the registration request, including a suggestion for a username that is not taken (e.g. "i_am_a_user" --> "i_am_a_user_3"). We do not provide live feedback to prevent probing of usernames.


### Wallet Address

The wallet address needs to be the one you want to use for participation in the XBR Network. 

The form automatically uses the currently selected account in MetaMask. If this is the one you want to use, just move on.

If this is not the case, then please switch the account in MetaMask and then press the "GET ADDRESS FROM METAMASK" button to update the account data.


### XBR Network Terms and Conditions

You need to accept our terms and conditions for the XBR Network. To do so just check the box at the bottom of the registration form. 

Note: A quick (not legally binding) summary of the terms would be "This is for testing only. Do not blame us if things go wrong. If you misbehave we may kick you off. You are not signing away anything by accepting these terms." 


### Signing the Registration Request

Once you have filled in everything and accepted the terms and conditions, the "SIGN UP" button becomes active.

Once you press this MetaMask pops up a confirmation dialog, since the request to sign up needs to be signed by you. Please confirm this by clicking "SIGN". 


### Registration Verification

Once you have signed the sign up request you should see a notice that the request has been sent successfully and that you will receive an email to verify your registration.

Note: The exception is if the username you chose is already taken - see above.

Check your email account for the registration verification mail. This should usually arrive in seconds, but there may be delays, so give it a few minutes at least before you assume things have failed.

In the mail there is a link for the verification of your account. This is best opened in the browser where you started the registration, since you need an additional log-in step when you open it somewhere else.

Click the link, or copy it into the address bar of the browser you want to use.

You should now see a notice that registration has been completed, and be forwarded to the XBR network member page with information on your account.

## Joining an IDMA Test Data Market

The available data markets for joining are listed on the XBR network members page. 

You participate in the IDMA, you need to join one IDMA test data market. These are clearly named.

To start joining one, simply click on the "Join" button.

You are then asked to read the market terms and conditions. For the IDMA test data markets these include the IDMA competition terms. 

We encourage you to read these. For those unwilling to do so, the (not legally binding) summary is "This is for the competition only, and not for any production use. Development is ongoing, so do not blame us if things go wrong. Behave fairly or get kicked off. We get some rights in what you develop, but purely for promotional use, and some minor cooperation by you in promotion may be required. These rights do not keep you from doing whatever you want with your development results."

Once you have accepted the terms, you need to sign the joining request with MetaMask. Just click on the "SIGN" button in the confirmation window that pops up.

Once you have signed the request you should see a confirmation screen which tells you that a verification email has been sent.

Check your email and click on the link in the verification mail. This takes you back to the XBR Network members page. In the listing of the test data markets, the button for the market you have just joined now reads "ACCESS". Click on it do just that.


## Accessing an IDMA Test Data Market

Once you have joined, you can accees the IDMA test data market.

The IDMA test data markets are run on a different domain from the XBR network, so you first need to allow the site for the market you have joined to connect with MetaMask. Click "CONNECT" on the MetaMask confirmation dialog that pops up. 

You then need to sign a MetaMask request that confirms to the test data market that you want to access it in this browser.


## Next Steps

You can explore the demo code in this repository, read the documentation for the XBR data market API - and get our demo application up and running so that you can start experimenting based on working code.
