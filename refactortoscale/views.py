#----------------------------------------------------------------------
# Copyright (c) 2018, Persistent Objects Ltd https://p-o.co.uk/
#
# License: BSD
#----------------------------------------------------------------------
"""Views for Refactoring for Scale"""

import logging
import pika

from django.shortcuts import render
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, Template
from refactortoscale.models import FRUIT_CHOICES
from refactortoscale.models import Preference, ActivityLog, SqlQueue

logger = logging.getLogger(__name__)

def home(request):
    """Home page"""
    context = {}
    return render(request, 'refactortoscale/home.html', context)

def submitbasic(request):
    """Basic submit page"""
    context = {
            "type": "basic",
            "choices": FRUIT_CHOICES,
    }
    if request.method == 'POST': # If the form has been submitted...
        try:
            p = Preference()
            p.name = request.POST['name']
            p.email = request.POST['email']
            p.fruit = request.POST['fruit']
            p.save()
            p.sendemail()
            request.session['preference_id'] = p.id
        except:
            msg_error = u'Something went wrong saving basic preference'
            logger.error(msg_error)
            messages.add_message(request, messages.ERROR, msg_error)
            a = ActivityLog(pref=self, message=msg_error)
            a.save()
            return render(request, 'error.html', context)
        return HttpResponseRedirect(reverse('thanks'))
    return render(request, 'refactortoscale/choices.html', context)

def submitsql(request):
    """SQL submit page"""
    context = {
            "type": "sql",
            "choices": FRUIT_CHOICES,
    }
    if request.method == 'POST': # If the form has been submitted...
        p = None
        try:
            # save preference
            p = Preference()
            p.name = request.POST['name']
            p.email = request.POST['email']
            p.fruit = request.POST['fruit']
            p.save()
            # Save the newly created preference in the session
            # so it can be used again
            request.session['preference_id'] = p.id
            # Add a task to the Sql queue to send a confirmation email
            q = SqlQueue()
            q.pref = p
            q.save()
        except:
            msg_error = u'Something went wrong saving the sql queue preference task'
            logger.error(msg_error)
            messages.add_message(request, messages.ERROR, msg_error)
            a = ActivityLog(pref=p, message=msg_error)
            a.save()
            return render(request, 'error.html', context)
        return HttpResponseRedirect(reverse('thanks'))
    return render(request, 'refactortoscale/choices.html', context)

def submitmq(request):
    """Message queue submit page"""
    context = {
            "type": "mq",
            "choices": FRUIT_CHOICES,
    }
    if request.method == 'POST': # If the form has been submitted...
        p = None
        try:
            # save preference
            p = Preference()
            p.name = request.POST['name']
            p.email = request.POST['email']
            p.fruit = request.POST['fruit']
            p.save()
            # Save the newly created preference in the session
            # so it can be used again
            request.session['preference_id'] = p.id
        except:
            msg_error = u'Something went wrong saving the message queue preference task'
            logger.error(msg_error)
            messages.add_message(request, messages.ERROR, msg_error)
            a = ActivityLog(pref=p, message=msg_error)
            a.save()
            return render(request, 'error.html', context)

        # Add a task to the message queue to send a confirmation email
        credentials = pika.credentials.PlainCredentials(
            settings.AMQP_USERNAME,
            settings.AMQP_PASSWORD
        )
        #        credentials=credentials,
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=settings.AMQP_HOST,
            )
        )

        try:
            channel = connection.channel()
            channel.queue_declare(queue=settings.AMQP_QUEUE, durable=True)
            channel.basic_publish(exchange='',
                routing_key=settings.AMQP_QUEUE,
                body=str(p.id),
                properties=pika.BasicProperties(
                    delivery_mode = 2, # make message persistent
                ), mandatory=True, immediate=False)
            logger.info("Queued message task for {} {} {}".format(p.id, p.name, p.email))
        except:
            msg_error = u'Something went wrong saving the message queue preference task'
            logger.error(msg_error)
            messages.add_message(request, messages.ERROR, msg_error)
            a = ActivityLog(pref=p, message=msg_error)
            a.save()
            return render(request, 'error.html', context)

        channel.close()
        connection.close()
        return HttpResponseRedirect(reverse('thanks'))
    return render(request, 'refactortoscale/choices.html', context)

def thanks(request):
    """Confirmation page"""
    context = {}
    if 'preference_id' in request.session:
        preference_id = int(request.session['preference_id'])
        p = Preference.objects.get(pk=preference_id)
        context = {
            "preference": p,
        }
    return render(request, 'refactortoscale/thanks.html', context)
