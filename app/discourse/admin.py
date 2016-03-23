from flask import flash, redirect, url_for
from flask_admin import Admin, BaseView, expose

from ..admin import AdminPermissionRequiredMixin
from . import models

class DiscourseView(AdminPermissionRequiredMixin, BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/discourse_index.html')

    @expose('/topics/recache', methods=['POST'])
    def recache_topics(self):
        models.DiscourseTopicEvent.update()
        flash('Discourse topics recached.')
        return redirect(url_for('discourse_admin.index'))
