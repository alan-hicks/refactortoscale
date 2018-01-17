import signal, os
import logging

from django.core.management.base import BaseCommand, CommandError
from refactortoscale.models import ActivityLog, Preference, SqlQueue
from refactortoscale.models import STATUS_TODO, STATUS_INPROGRESS
from refactortoscale.models import STATUS_ERROR, STATUS_COMPLETE
from time import sleep

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run Sql queue runner'

    # Flag to gracefully stop
    continue_running = True

    def handlesig(self, *args, **options):
        """Handle an interrupt"""
        Command.continue_running = False

    # Capture SIGINT
    signal.signal(signal.SIGINT, handlesig)

    def handle(self, *args, **options):
        """Fetch the first available task, then repeat until done"""
        while self.continue_running:
            # Get a batch of available tasks
            msg_error = u'Fetching next batch of tasks'
            logger.debug(msg_error)
            # The following is suitable for a single queue runner
            q = SqlQueue.objects.filter(status=STATUS_TODO)[:10]
            # The following is suitable for databases that support
            # select_for_update(skip_locked=True) such as PostgreSQL and Oracle
            # and allow for multiple queue runners
            #q = SqlQueue.objects.select_for_update(
            #        skip_locked=True).filter(
            #        status=STATUS_TODO)[:10]
            if len(q) == 0:
                # If there is nothing to process,
                # then be kind and pause for a few seconds
                sleep(30)
            for task in q:
                if not self.continue_running:
                    self.stdout.write('Ok, stopping now')
                    return 0
                # Update this task to show we are working on it
                # update status = busy
                task.status = STATUS_INPROGRESS
                task.save()
                pref = Preference.objects.get(pk=task.pref.id)
                try:
                    pref.sendemail()
                    msg_error = u'Fruit email sent'
                    logger.debug(msg_error)
                    a = ActivityLog(pref=pref, message=msg_error)
                    a.save()
                    task.status = STATUS_COMPLETE
                    task.save()
                except:
                    msg_error = u'Something went wrong sending sql email'
                    logger.error(msg_error)
                    task.status = STATUS_ERROR
                    task.save()
                    a = ActivityLog(pref=pref, message=msg_error)
                    a.save()

