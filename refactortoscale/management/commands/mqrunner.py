import logging
import pika

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from refactortoscale.models import ActivityLog, Preference
from refactortoscale.models import STATUS_TODO, STATUS_INPROGRESS
from refactortoscale.models import STATUS_ERROR, STATUS_COMPLETE
from time import sleep

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    def __init__(self):
        # Class instance variables
        self._channel=None

    help = 'Run message queue runner'

    def consumer_callback(self, channel, method_frame, header_frame, body):
        """Process messages from the queue"""
        logger.debug(method_frame.delivery_tag)

        id = 0
        try:
            id = int(body)
            msg_error = "Successfully found message {}".format(id)
            logger.debug(message_error)
        except:
            message_error = "Unable to find message"
            logger.error(msg_error)

        if id:
            pref = Preference.objects.get(pk=id)
            try:
                pref.sendemail()
                msg_error = u'Fruit email sent'
                logger.debug(msg_error)
                a = ActivityLog(pref=pref, message=msg_error)
                a.save()
                channel.basic_ack(delivery_tag = method_frame.delivery_tag)
            except Exception as e:
                msg_error = u"Failed to send message: {}: {}".format(date_now, e)
                logger.error(msg_error)
                a = ActivityLog(pref=pref, message=msg_error)
                a.save()
                channel.basic_nack(delivery_tag=method_frame.delivery_tag)
            except:
                msg_error = u"Failed"
                logger.error(msg_error)
                a = ActivityLog(pref=pref, message=msg_error)
                a.save()
                channel.basic_nack(delivery_tag=method_frame.delivery_tag)

    def handle(self, *args, **options):
        """Initialise the queue and start accepting messages"""
        logger.debug("Initial program setup")

        credentials = pika.credentials.PlainCredentials(
            settings.AMQP_USERNAME,
            settings.AMQP_PASSWORD
        )
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=settings.AMQP_HOST,
                virtual_host='/',
            ),
        )
        self._channel = connection.channel()
        self._channel.basic_qos(prefetch_count=1)
        self._channel.queue_declare(queue=settings.AMQP_QUEUE, durable=True)

        logger.debug("Waiting for messages")
        consumer_tag = self._channel.basic_consume(
            self.consumer_callback,
            queue=settings.AMQP_QUEUE
        )
        logger.debug("Consumer tag: {}".format(consumer_tag))

        try:
            self._channel.start_consuming()
        except KeyboardInterrupt:
            self._channel.stop_consuming()
            requeued_messages = self._channel.cancel()
            msg_error = 'Requeued {} messages'.format(requeued_messages)
            logger.warning(msg_error)
        except InterruptedError:
            self._channel.stop_consuming()
            requeued_messages = self._channel.cancel()
            msg_error = 'Requeued {} messages'.format(requeued_messages)
            logger.warning(msg_error)
        connection.close()
        msg_error = 'Exited normally'
        logger.debug(msg_error)

