#! usr/bin/python3
# -*- coding: utf-8 -*-
#
# Flicket - copyright Paul Bourne: evereux@gmail.com

from flask import redirect, url_for, flash, render_template, g
from flask_babel import gettext
from flask_login import login_required

from application import app, db
from application.flicket.forms.flicket_forms import ChangeQueueForm
from application.flicket.models.flicket_models import FlicketTicket, FlicketQueue, FlicketStatus, FlicketSubscription
from application.flicket.models.flicket_user import FlicketUser
from application.flicket.scripts.flicket_functions import add_action
from application.flicket.scripts.email import FlicketMail
from . import flicket_bp


# tickets main
@flicket_bp.route(app.config['FLICKET'] + 'ticket_queue/<int:ticket_id>/', methods=['GET', 'POST'])
@login_required
def ticket_queue(ticket_id=False):
    form = ChangeQueueForm()
    ticket = FlicketTicket.query.get_or_404(ticket_id)

    if ticket.current_status.status == 'Closed':
        flash(gettext("Can't change the queue on a closed ticket."))
        return redirect(url_for('flicket_bp.ticket_view', ticket_id=ticket_id))

    if form.validate_on_submit():
        queue = FlicketQueue.query.filter_by(queue=form.queue.data).one()

        if ticket.category_id == queue.category_id:
            flash(gettext('Queue is already assigned to ticket.'))
            return redirect(url_for('flicket_bp.ticket_view', ticket_id=ticket.id))

        # set status to open
        status = FlicketStatus.query.filter_by(status='Open').first()
        # change queue of the ticket
        ticket.category_id = queue.category_id
        ticket.current_status = status

        # add action record
        # TODO: update add_action function and FlicketAction model to support new action
        # until it is done, and new action ready for use, this will not be merged into
        # 0.2.1 branch
        #add_action(action='queue', ticket=ticket, recipient=g.user)

        # subscribe to the ticket
        if not ticket.is_subscribed(g.user):
            subscribe = FlicketSubscription(
                ticket=ticket,
                user=g.user
            )
            db.session.add(subscribe)

        db.session.commit()

        # send email to state ticket has been assigned.
        f_mail = FlicketMail()
        f_mail.queue_ticket(ticket)

        flash(gettext('You changed queue of ticket: %(value)s', value=ticket.id))
        return redirect(url_for('flicket_bp.ticket_view', ticket_id=ticket.id))

    title = gettext('Change Queue of Ticket')

    return render_template("flicket_queue.html", title=title, form=form, ticket=ticket)