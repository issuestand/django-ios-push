django-ios-push
=============

A Django Application for contacting the Apple Push Service and maintaining a list of iOS devices.

Based on Lee Packham's [django-iphone-push](https://github.com/leepa/django-iphone-push) but **it's not compatibile!**

Changes from original:
* Cleaner names
* It works with iPhones, iPods Touch and iPads, so all *"iPhone"* references were changed to *"Device"* or *"iOS"*
* Filtering in admin
* iOS 5 Newsstand notifications support

Usage
-----
First of all, you need to create certificates. A great tutorial is available here: http://www.macoscoders.com/2009/05/17/iphone-apple-push-notification-service-apns/

Then you have to add **iospush** to **INSTALLED_APPS** and add some configuration to **settings.py**:

	# Full path to the APN Certificate / Private Key .pem
	APN_SANDBOX_PUSH_CERT = os.path.join(PROJECT_ROOT, "iphone_ck.pem")
	APN_LIVE_PUSH_CERT = os.path.join(PROJECT_ROOT, "iphone_live.pem")
	
	# Set this to the hostname for the outgoing push server
	APN_SANDBOX_HOST = 'gateway.sandbox.push.apple.com'markdown
	APN_LIVE_HOST = 'gateway.push.apple.com'
	
	# Set this to the hostname for the feedback server
	APN_SANDBOX_FEEDBACK_HOST = 'feedback.sandbox.push.apple.com'
	APN_LIVE_FEEDBACK_HOST = 'feedback.push.apple.com'

Now is time to **manage.py syncdb** and add some devices to database (if you're running in sandbox, set **is\_test\_device = True** to send data to the right place).
Try to send some notifications:

	from iospush import models
	
	device = models.Device.objects.all()[:1]
	# Simple notification
    device.send_message(alert='My hovercraft is full of eels')
    # Notification with badge number
    device.send_message(alert='Answer to everything!', badge=42)
    # Notification with custom sound
    device.send_message(alert='My sound', sound='mysound')
    # Newsstand content availability notification
    device.send_message(alert='New issue', content_available=True)
    # This notification will expire after Tue, 26 Mar 2013 22:10:54 GMT
    device.send_message(alert='New issue', expiry=1364335854)

Sending mass notification is also simple:
	
	models.sendMessageToPhoneGroup(models.Device.objects.all(), alert='Greetings to you all!', sandbox=True)
	
In case of need to communicate with different iOS applications, which requires using different certificates, you can specify it when sending notification:

	device.send_message(alert='Test', custom_cert=os.path.join(settings.PROJECT_PATH, 'custom_cert.pem'))


LICENCE
-------

Copyright (C) 2012 Wojtek Siudzinski <wojtek@appsome.co>, [Appsome](http://appsome.co)

Licensed under the Apache License, Version 2.0: http://www.apache.org/licenses/LICENSE-2.0