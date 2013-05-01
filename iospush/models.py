"""
django-ios-push - Django Application for doing iOS Push Notifications
Originally written by Lee Packham (http://leenux.org.uk/ http://github.com/leepa)
Updated by Wojtek 'suda' Siudzinski <wojtek@appsome.co>

(c)2009 Lee Packham - ALL RIGHTS RESERVED
May not be used for commercial applications without prior concent.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone

from socket import socket

import datetime
import struct
import ssl
import binascii
import math

# Handle Python 2.5 / 2.6 seamlessly
try:
    import json
except ImportError:
    import simplejson as json

class Device(models.Model):
    """
    Represents an iPhone used to push
    
    device_token - the Device's token (64 chars of hex)
    last_notified_at - when was a notification last sent to the phone
    is_test_device - is this a phone that should be included in test runs
    notes - just a small notes field so that we can put in things like "Lee's iPhone"
    failed_phone - Have we had feedback about this phone? If so, flag it.
    """
    device_token = models.CharField(blank=False, max_length=64)
    last_notified_at = models.DateTimeField(blank=True, default=timezone.now())
    is_test_device = models.BooleanField(default=False)
    notes = models.CharField(blank=True, max_length=100)
    failed = models.BooleanField(default=False)
    platform = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        unique_together = (('device_token', 'is_test_device'),)
    
    def _getApnHostName(self):
        """
        Get the relevant hostname for the instance of the phone
        """
        if self.is_test_device:
            return settings.APN_SANDBOX_HOST
        else:
            return settings.APN_LIVE_HOST
            
    def _getApnCertPath(self):
        """
        Get the relevant certificate for the instance of the phone
        """
        if self.is_test_device:
            return settings.APN_SANDBOX_PUSH_CERT
        else:
            return settings.APN_LIVE_PUSH_CERT
    
    def send_message(self, alert, badge=0, sound="chime", content_available=False,
                        custom_params={}, action_loc_key=None, loc_key=None,
                        loc_args=[], passed_socket=None, custom_cert=None,
                        identifier=0, expiry=0):
        """
        Send a message to an iPhone via the APNS protocol.

        Steps within this function include;

            1) Build the Binary Interface Notification packets.
            2) Transmit packets to APNS server.
            3) Receive APNS server response.
            4) Return transmission outcome.

        Further details of the APNS Notification packets can be found on the Apple developer website, at:
            http://developer.apple.com/library/mac/#documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/Chapters/CommunicatingWIthAPS.html#//apple_ref/doc/uid/TP40008194-CH101-SW1

        Args:
            alert: The message you want to send
            badge: Numeric badge number you wish to show, 0 will clear it
            sound: chime is shorter than default! Replace with None/"" for no sound
            content_available: newsstand notification about new content available
            sandbox: Are you sending to the sandbox or the live server
            custom_params: A dict of custom params you want to send
            action_loc_key: As per APN docs
            loc_key: As per APN docs
            loc_args: As per APN docs, make sure you use a list
            passed_socket: Rather than open/close a socket, use an already open one
            identifier: An arbitrary value that identifies this notification
            expiry: A fixed UNIX epoch date expressed in seconds (UTC) that identifies when the notification is no longer valid and can be discarded

        Returns:
            True if APNS transmission is successful, and an exception if APNS transmission fails.

        Raises:
            TypeError: if argument, alert, is of type, None.
            ValueError: if variable, s_payload, is greater than 256 bytes.
            Exception: if APNS server response code is, 1. ('Processing error')
            Exception: if APNS server response code is, 2. ('Missing device token')
            Exception: if APNS server response code is, 3. ('Missing topic')
            Exception: if APNS server response code is, 4. ('Missing payload')
            Exception: if APNS server response code is, 5. ('Invalid token size')
            Exception: if APNS server response code is, 6. ('Invalid topic size')
            Exception: if APNS server response code is, 7. ('Invalid payload size')
            Exception: if APNS server response code is, 8. ('Invalid token')
            Exception: if APNS server response code is anything other than 1 - 8. ('None (unknown)')
            SSLError: if APNS server does not respond.
        """
        aps_payload = {}

        alert_payload = alert
        if action_loc_key or loc_key or loc_args:
            alert_payload = {'body' : alert}
            if action_loc_key:
                alert_payload['action-loc-key'] = action_loc_key
            if loc_key:
                alert_payload['loc-key'] = loc_key
            if loc_args:
                alert_payload['loc-args'] = loc_args

        aps_payload['alert'] = alert_payload
        
        if badge:
            aps_payload['badge'] = badge
        
        if sound:
            aps_payload['sound'] = sound        
        
        if content_available:
            aps_payload['content-available'] = 1
        
        payload = custom_params
        payload['aps'] = aps_payload
        
        # This ensures that we strip any whitespace to fit in the 
        # 256 bytes
        s_payload = json.dumps(payload, separators=(',',':'), ensure_ascii=False).encode('utf8')
        
        fmt = "!cIIH32sH%ds" % len(s_payload)
        command = '\x01'
        msg = struct.pack(fmt, command, identifier, expiry, 32, binascii.unhexlify(self.device_token), len(s_payload), s_payload)
        
        if passed_socket:
            c = passed_socket
        else:
            s = socket()
            if custom_cert is None:
                custom_cert = self._getApnCertPath()
            c = ssl.wrap_socket(s,
                                ssl_version=ssl.PROTOCOL_SSLv3,
                                certfile=custom_cert)
            c.connect((self._getApnHostName(), 2195))

        c.write(msg)
        c.settimeout(1)
        try:                
            response = c.read()
            print len(response)
            if len(response) > 0:
                response_command, response_status, response_identifier = struct.unpack("!BBI", response)
                if response_command == 8:
                    if response_status == 1:
                        raise Exception('Processing error')
                    elif response_status == 2:
                        raise Exception('Missing device token')
                    elif response_status == 3:
                        raise Exception('Missing topic')
                    elif response_status == 4:
                        raise Exception('Missing payload')
                    elif response_status == 5:
                        raise Exception('Invalid token size')
                    elif response_status == 6:
                        raise Exception('Invalid topic size')
                    elif response_status == 7:
                        raise Exception('Invalid payload size')
                    elif response_status == 8:
                        raise Exception('Invalid token')
                    else:
                        raise Exception('None (unknown)')
        except ssl.SSLError as e:
            pass

        if not passed_socket:
            c.close()            
        
        return True

    def __unicode__(self):
        return u"Device %s" % self.device_token
        
def sendMessageToPhoneGroup(devices_list, alert, badge=0, sound="chime", content_available=False,
                            custom_params={}, action_loc_key=None, loc_key=None,
                            loc_args=[], sandbox=False, custom_cert=None,
                            identifier=0, expiry=0):
    """
    See the syntax for send_message, the only difference is this opens
    one socket to send them all.
    
    The caller must ensure that all phones are the same sandbox level
    otherwise it'll end up sending messages to the wrong service.
    """

    if sandbox:
        host_name = settings.APN_SANDBOX_HOST
    else:
        host_name = settings.APN_LIVE_HOST

    if custom_cert is None:
        if sandbox:
            custom_cert = settings.APN_SANDBOX_PUSH_CERT
        else:
            custom_cert = settings.APN_LIVE_PUSH_CERT
    
    chunkSize = 75
    currentChunk = 0

    while (currentChunk <= math.ceil(devices_list.count() / chunkSize)):
        s = socket()
        c = ssl.wrap_socket(s,
                            ssl_version=ssl.PROTOCOL_SSLv3,
                            certfile=custom_cert)
        c.connect((host_name, 2195))
        
        rangeMin = chunkSize * currentChunk
        rangeMax = rangeMin + chunkSize

        for device in devices_list[rangeMin:rangeMax]:
            device.send_message(alert, badge=badge, sound=sound, content_available=content_available, custom_params=custom_params,
                                action_loc_key=action_loc_key, loc_key=loc_key, loc_args=loc_args, passed_socket=c,
                                identifier=identifier, expiry=expiry)

        c.close()
        currentChunk += 1
    
def doFeedbackLoop(sandbox = False):
    """
    Contact the APN server and ask for feedback on things that
    have not gone through so the iPhone list can be updated accordingly
    
    Does two things:
        1. Find all associated iPhone objects and set failed_device to True
        2. Return a dict of hexlified push IDs with the time_t
        
    Annoyingly, I've had to stub this out for now as it seems that sandbox
    feedback service just doesn't do anything at all!
    
    If Apple fix that, I can test/debug a lot easier. Until then...
    """
    raise NotImplementedError
    
    if sandbox:
        host_name = settings.APN_SANDBOX_FEEDBACK_HOST
        cert_path = settings.APN_SANDBOX_PUSH_CERT
    else:
        host_name = settings.APN_LIVE_FEEDBACK_HOST
        cert_path = settings.APN_LIVE_PUSH_CERT

    s = socket()
    c = ssl.wrap_socket(s,
                        ssl_version=ssl.PROTOCOL_SSLv3,
                        certfile=settings.APN_LIVE_PUSH_CERT)
    c.connect((settings.APN_FEEDBACK_HOST, 2196))

    full_buf = ''
    while 1:
        tmp = c.recv(38)
        print tmp
        if not tmp:
            break
        else:
            full_buf += tmp
        
    c.close()
