from blinker import Namespace

signals = Namespace()

user_changed_profile = signals.signal('user-changed-profile')

user_completed_registration = signals.signal('user-completed-registration')