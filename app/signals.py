from blinker import Namespace

signals = Namespace()

user_changed_profile = signals.signal('user-changed-profile')
