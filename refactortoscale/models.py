#----------------------------------------------------------------------
# Copyright (c) 2018, Persistent Objects Ltd https://p-o.co.uk/
#
# License: BSD
#----------------------------------------------------------------------

"""Models for Refactor to Scale"""

import logging

from django.conf import settings
from django.core.mail import EmailMessage, BadHeaderError
from django.db import models
from django.template.loader import get_template

logger = logging.getLogger(__name__)

FRUIT_PLEASE_CHOOSE=''
FRUIT_APPLE='AP'
FRUIT_BANANA='BA'
FRUIT_ORANGE='OR'
FRUIT_STRAWBERRY='ST'
FRUIT_CHOICES=[ 
    (FRUIT_PLEASE_CHOOSE, 'Please choose a fruit'),
    (FRUIT_APPLE, 'Apple'),
    (FRUIT_BANANA, 'Banana'),
    (FRUIT_ORANGE, 'Orange'),
    (FRUIT_STRAWBERRY, 'Strawberry'),
]

STATUS_TODO=0
STATUS_INPROGRESS=10
STATUS_ERROR=20
STATUS_COMPLETE=30

class Preference(models.Model):
    """Model to capture a fruit preference"""
    name = models.CharField(max_length=75)
    email = models.EmailField(max_length=250)
    fruit = models.CharField(max_length=2, choices=FRUIT_CHOICES, default=FRUIT_PLEASE_CHOOSE)

    def __unicode__(self):
        return self.name

    @property
    def fruit_name(self):
        """Return the full name of the fruit"""
        if self.fruit:
            chosenfruit = None
            chosenfruit = [  d for (c, d) in FRUIT_CHOICES if c == self.fruit]
            logger.debug(chosenfruit)
            if chosenfruit:
                return chosenfruit.pop()
        return self.name

    def sendemail(self):
        """Send email"""
        context = {
            "preference": self,
        }
        plaintext = get_template('refactortoscale/thanks.txt')
        text_content = plaintext.render(context)
        email_subject = u'Thanks for choosing {}'.format(self.fruit_name)
        msg = EmailMessage(
                subject=email_subject,
                body=text_content,
                from_email=settings.EMAIL_FROM,
                to=[self.email])
        try:
            msg.send()
            a = ActivityLog(pref=self, message=u'Thank you email sent')
            a.save()
            logger.info(u'Thank you email sent')
        except BadHeaderError as e:
            msg_error = u'Unable to send message: {}'.format(e)
            logger.error(msg_error)
            a = ActivityLog(pref=self, message=msg_error)
            a.save()
        except:
            msg_error = u'Unable to send message'
            logger.error(msg_error)
            a = ActivityLog(pref=self, message=msg_error)
            a.save()

class ActivityLog(models.Model):
    """Model for recording events"""
    pref = models.ForeignKey(Preference)
    message = models.TextField()

class SqlQueue(models.Model):
    """Model for feeding SQL queue runners"""
    pref = models.ForeignKey(Preference)
    status = models.SmallIntegerField(default=STATUS_TODO)
    queueid = models.SmallIntegerField(default=0)

