from django.db import models

from django.contrib.auth.models import User

#from fields import CreatedField, ModifiedField, AutoUserField
from base_classes import NameSlugBase, getCreationBase

nullblank = { 'null': True, 'blank': True }



class BaseIssue(NameSlugBase):
	description		= models.TextField(**nullblank)


class Polity(BaseIssue, getCreationBase('polity')):
	parent			= models.ForeignKey('Polity', **nullblank)
	members			= models.ManyToManyField(User)
	invite_threshold	= models.IntegerField(default=3)

	is_listed		= models.BooleanField(default=True)
	is_nonmembers_readable	= models.BooleanField(default=True)

	image			= models.ImageField(upload_to="polities", **nullblank)

	def is_member(user):
		return user in self.members


class Topic(BaseIssue, getCreationBase('topic')):
	polity			= models.ForeignKey(Polity)
	image			= models.ImageField(upload_to="polities", **nullblank)

class Issue(BaseIssue, getCreationBase('issue')):
	topics			= models.ManyToManyField(Topic)
	options			= models.ManyToManyField('VoteOption')

	def topics_str(self):
		return ', '.join(map(str, self.topics.all()))

	def polity(self):
		try:
			return self.topics.all()[0].polity
		except:
			return None

class Comment(getCreationBase('comment')):
	comment			= models.TextField()
	issue			= models.ForeignKey(Issue)

class Delegate(models.Model):
	user			= models.ForeignKey(User)
	delegate		= models.ForeignKey(User, related_name='delegate_user')
	base_issue		= models.ForeignKey(BaseIssue)
	class Meta:
		unique_together = (('user', 'base_issue'))

class VoteOption(NameSlugBase):
	pass

class Vote(models.Model):
	user			= models.ForeignKey(User)
	issue			= models.ForeignKey(Issue)
	option			= models.ForeignKey(VoteOption)
	cast			= models.DateTimeField(auto_now_add=True)
	class Meta:
		unique_together = (('user', 'issue'))


class MembershipVote(models.Model):
	voter			= models.ForeignKey(User, related_name="membership_granter")
	user			= models.ForeignKey(User, related_name="membership_seeker")
	polity			= models.ForeignKey(Polity)

	class Meta:
		unique_together = ( ("voter", "user", "polity"), )


class MembershipRequest(models.Model):
	requestor		= models.ForeignKey(User)
	polity			= models.ForeignKey(Polity)
	fulfilled		= models.BooleanField(default=False)
	fulfilled_timestamp	= models.DateTimeField(null=True)

	class Meta:
		unique_together = ( ("requestor", "polity"), )

	def votes(self):
		return MembershipVote.objects.filter(user=self.requestor, polity=self.polity).count()

	def get_fulfilled(self):
		# Recalculate at most once per hour.
		if self.fulfilled_timestamp == None or self.fulfilled_timestamp < datetime.now() - timedelta(seconds=3600):
			self.fulfilled = self.votes() >= self.polity.invite_threshold
			self.save()

		return self.fulfilled
