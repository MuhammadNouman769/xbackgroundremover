# Currently using Django's built-in auth.User (see forms.py SignUpForm).
# If you later need extra profile fields (avatar, plan, credits, etc.),
# add a Profile model here with a OneToOneField to auth.User and a
# post_save signal - keeping it separate avoids touching Django's own
# user table.
