import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from google.appengine.dist import use_library
use_library('django', '1.2')
import urllib
import operator
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users
from datetime import datetime,date

#Authorize if the current user is also an author of the same survey
def authUser(user,author):
	return (user == author) 

#Returns true if user is also an admin else false
def isAdmin(user):
	if user.nickname() == "abhinavsahai4u" :
		return True
	results = AdminModel.gql("WHERE username=:1", user.nickname())
	return results.count()!=0
# SurveyModel defines the data model for the Survey
# as it extends db.model the content of the class will automatically stored
class SurveyModel(db.Model):
	author = db.UserProperty(required=True)
	nick = db.StringProperty(required=True)
	surveyname = db.StringProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)
	expiry = db.DateProperty(default = datetime.date(datetime.strptime('2012-12-31', '%Y-%m-%d')))
	visibility = db.BooleanProperty(default = True) #means visible to all

# QuestionModel defines the data model for the Surveys questions
# as it extends db.model the content of the class will automatically stored
class QuestionModel(db.Model):
	sid = db.IntegerProperty(required=True)
	author = db.UserProperty(required=True)
	nick = db.StringProperty(required=True)
	questiondes = db.StringProperty(required=True)
	answerlist = db.StringListProperty(required=True)

# VoteModel defines the data model for the Votes from users
# as it extends db.model the content of the class will automatically stored
class VoteModel(db.Model):
	sid = db.IntegerProperty(required = True)
	qid = db.IntegerProperty(required=True)
	voter = db.UserProperty(required=True)
	answer = db.StringProperty(required=True)

# ResultModel defines the data model for storing the number of votes for answer choices
class ResultModel(db.Model):
	sid = db.IntegerProperty(required = True)
	qid = db.IntegerProperty(required=True)
	answer = db.StringProperty(required=True)
	count = db.IntegerProperty(default=0)

# AccessModel defines the data model for storing information of who can access which surveys
class AccessModel(db.Model):
	sid = db.IntegerProperty(required = True)
	nick = db.StringProperty(required = True)

# AdminModel defines the data model for storing the site super users
class AdminModel(db.Model):
	username = db.StringProperty(required = True)
	position = db.StringProperty(default = "admin")

# LoginModel defines the data model for storing login times for users
class LoginModel(db.Model):
	username = db.StringProperty(required=True)
	lastLogin = db.DateTimeProperty(auto_now_add=True)

class MainPage(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		#userobj = AdminModel(username="abhinavsahai4u")
		#userobj.put()
		#userobj = AccessModel(sid=100,nick="abhinavsahai4u")
		#userobj.put()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		lastLogin=""
		admin = "false"
		surveys = ""
		if user:
			result = LoginModel.gql("WHERE username=:1", user.nickname())
			if result.count()!=0 :
				userEntity = result.get()
				lastLogin = userEntity.lastLogin
				userEntity.delete()
			userobj = LoginModel(username=user.nickname())
			userobj.put()
				
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			if isAdmin(user):
				admin = "true"
				#self.response.out.write("Admin Interface")
			surveys = db.GqlQuery("SELECT * FROM SurveyModel where author=:1", user)
		values = {'admin':admin,
			'surveys':surveys,
            'active': "home",
            'user':user,
            'url':url,
            'url_linktext':url_linktext,
            'lastLogin' : lastLogin			  
		}

		self.response.out.write(template.render('html/header.html', values))
		self.response.out.write(template.render('html/home.html', values))
		self.response.out.write(template.render('html/footer.html', ""))

#This class handles the home page requests
class HomePage(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		admin = "false"
		surveys = ""
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			if isAdmin(user):
				admin = "true"
				#self.response.out.write("Admin Interface")				

			surveys = db.GqlQuery("SELECT * FROM SurveyModel where author=:1", user)
		values = {'admin':admin,
			'surveys':surveys,
            'active': "homepage",
            'user':user,
            'url':url,
            'url_linktext':url_linktext				  
		}
		
		self.response.out.write(template.render('html/header.html', values))
		self.response.out.write(template.render('html/home.html', values))
		self.response.out.write(template.render('html/footer.html', ""))

#Class handles user management request 
class UserManagement(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		admin = "false"
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			if isAdmin(user):
				admin = "true"
				administrators = db.GqlQuery("SELECT * FROM AdminModel")
				values = {'admin':admin,
					'administrators':administrators,
		            'active': "userM",
		            'user':user,
		            'url':url,
		            'url_linktext':url_linktext				  
				}
				#self.response.out.write("Admin Interface")
			else :
				self.redirect("/error?code=2")
		else :
			values = {'admin':admin,
					'user':user,
            		'url':url,
              		'url_linktext':url_linktext
              		}
		self.response.out.write(template.render('html/header.html', values))
		self.response.out.write(template.render('html/userManagement.html', values))
		self.response.out.write(template.render('html/footer.html', ""))
#Revoking admin rights
class RemoveAdmin(webapp.RequestHandler):
	def post(self):
		user = users.get_current_user()
		raw_id = self.request.get('aid')
		if not raw_id and not user and not isAdmin(user) :
			self.redirect("/error?code=2")
		else :
			adminid = long(raw_id)
			
			#Can't remove me as admin
			adminObj = AdminModel.get_by_id(adminid)
			if adminObj.username != "abhinavsahai4u":
				adminObj.delete()
			self.redirect("/userM")

#Add new users as site admin
class AddAdmin(webapp.RequestHandler):
	def post(self):
		user = users.get_current_user()
		raw_name = self.request.get('nickname')
		if not raw_name and not user and not isAdmin(user) :
			self.redirect("/error?code=2")
		else :
			username = str(raw_name)
			#check to ensure there is no previous entry
			check = AdminModel.gql("WHERE username=:1",username)
			if check.count() != 0: #already added
				self.redirect("/error?code=4")
			else :
				adminObj = AdminModel(username=username)
				adminObj.put()
				self.redirect("/userM")

#A case insensitive search to find matching surveys
class Search(webapp.RequestHandler):
	def post(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		admin = "false"
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			if isAdmin(user):
				admin = "true"
				#self.response.out.write("Admin Interface")
			searchword = str(self.request.get('searchfield')).lower()
			if admin == "true":
				surveys = db.GqlQuery("SELECT * FROM SurveyModel")
			else :
				surveys = db.GqlQuery("SELECT * FROM SurveyModel where visibility=True")		
			
			matchlist = []
			for survey in surveys :
				name = survey.surveyname.lower()
				if name.find(searchword,0,len(name)) != -1 :
					matchlist.append(survey)
					
			if admin == "false":
				queryAccess = AccessModel.gql("WHERE nick=:1",user.nickname())
				for result in queryAccess:
					survey = SurveyModel.get_by_id(result.sid)
					name = survey.surveyname.lower()
					if name.find(searchword,0,len(name)) != -1 :
						matchlist.append(survey)
	
			values = {
				'surveys':surveys,
				'matchlist':matchlist,
	            'active': "search",
	            'user':user,
	            'url':url,
	            'url_linktext':url_linktext				  
			}
		else :
			values = {'admin':admin,
					'user':user,
	        		'url':url,
	          		'url_linktext':url_linktext
	          	}
		self.response.out.write(template.render('html/header.html', values))
		self.response.out.write(template.render('html/search.html', values))
		self.response.out.write(template.render('html/footer.html', ""))
		
	def get(self):
		self.redirect("/")

class CreateSurvey(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		admin = "false"
		
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			if isAdmin(user):
				admin = "true"
				#self.response.out.write("Admin Interface")
		values = {'admin': admin,
            'active': "create",
            'user':user,
            'url':url,
            'url_linktext':url_linktext	
		}
		self.response.out.write(template.render('html/header.html', values))
		self.response.out.write(template.render('html/create.html', values))
		self.response.out.write(template.render('html/footer.html', ""))
	
	def post(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		admin = "false"
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			if isAdmin(user):
				admin = "true"
				#self.response.out.write("Admin Interface")

		values = {'admin': admin,
            'active': "create",
            'user':user,
            'url':url,
            'url_linktext':url_linktext	
		}
		survey_name = self.request.get('surveyname')
		raw_expiry = self.request.get('expiry')
		if not survey_name :
			self.redirect("error?code=3")
		else :
			if raw_expiry:
				expiry = datetime.date(datetime.strptime(str(raw_expiry), '%Y-%m-%d'))
			else :
				expiry = datetime.date(datetime.strptime('2012-12-31', '%Y-%m-%d'))
			#check whether the survey name already exists
			checkname = SurveyModel.gql("WHERE surveyname=:1 and author=:2",survey_name,user)
			if checkname.count() !=0 : #survey exists with that name
				self.redirect("error?code=1")
			else :
				survey = SurveyModel(author=user,
									nick = user.nickname(),
									surveyname=survey_name,
									expiry=expiry)
				survey.put()
				
				self.response.out.write(template.render('html/header.html', values))
				self.response.out.write("""<center><h3>The survey %s has been successfully created. 
				Please visit <a href="/manageSurvey">Manage Survey</a> to add questions</h3></center>""" % survey_name)
				self.response.out.write(template.render('html/footer.html', ""))

class EditSurvey(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		admin = "false"
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			if isAdmin(user):
				admin = "true"
				#self.response.out.write("Admin Interface")

			raw_id = self.request.get('id')
			if not raw_id :
				self.redirect("/error?code=2")
			else :
				surveyid = int(raw_id)
				survey = SurveyModel.get_by_id(surveyid)
				#user has to be the author or admin
				if not authUser(user, survey.author) and not isAdmin(user) :
					self.redirect("/error?code=2")
				else :
					questions = db.GqlQuery("SELECT * FROM QuestionModel where sid =:1 and author=:2",
										surveyid, survey.author);
			
					values = {'admin': admin,
						'survey':survey,
						'questions': questions,
			            'active': "edit",
			            'url':url,
			            'user':user,
			            'url_linktext':url_linktext	
					}
		else :
			values = {'admin':admin,
					'user':user,
            		'url':url,
              		'url_linktext':url_linktext
              		}
		self.response.out.write(template.render('html/header.html', values))
		self.response.out.write(template.render('html/edit.html', values))
		self.response.out.write(template.render('html/footer.html', ""))
		
				

class DeleteQuestion(webapp.RequestHandler):
	def post(self):
		questionid = int(self.request.get('questionid'))
		questionEntity = QuestionModel.get_by_id(questionid)
		user = users.get_current_user()
		if authUser( user, questionEntity.author) or isAdmin(user):
			votes = VoteModel.gql("WHERE qid=:1",questionid)
			#delete all votes
			for vote in votes:
				vote.delete()
			results = ResultModel.gql("WHERE qid=:1",questionid)
			#delete results
			for result in results:
				result.delete()
			questionEntity.delete()
			raw_id = self.request.get('surveyid');
			surveyid = int(raw_id)
			self.redirect('/edit?' + urllib.urlencode({'id':surveyid }))
		else :
			self.redirect("/error?code=2")
	def get(self):
		self.redirect("/")

class DeleteSurvey(webapp.RequestHandler):
	def get(self):
		surveyid = int(self.request.get('id'))
		survey = SurveyModel.get_by_id(surveyid)
		author = survey.author
		user = users.get_current_user()
		#Deleting Survey Questions
		if (author == user or isAdmin(user)):
			questions = QuestionModel.gql("WHERE sid=:1 and author=:2", surveyid, author)
			for question in questions:
				votes = VoteModel.gql("WHERE qid=:1",long(question.key().id()))
				for vote in votes:
					vote.delete()
				results = ResultModel.gql("WHERE qid=:1",long(question.key().id()))
				for result in results:
					result.delete()
				question.delete()
		
			survey.delete()
			self.redirect("/manageSurvey")
		else :
			self.redirect("error?code=2")

class RemoveUser(webapp.RequestHandler):
	def post(self):
		user = users.get_current_user()
		raw_id = self.request.get('id')
		if not raw_id or not user:
			self.redirect("/error?code=2")
		else:
			surveyid = int(raw_id)
			survey = SurveyModel.get_by_id(surveyid)
			#user has to be the author or admin
			if not authUser(user, survey.author) and not isAdmin(user) :
				self.redirect("/error?code=2")
			else :
				nickname = self.request.get('nickname')
				if not nickname:
					self.redirect("/error?code=2")
				else:
					results = AccessModel.gql("WHERE sid=:1 AND nick=:2", surveyid,nickname)
					for result in results :
						result.delete()
					self.redirect("/perm?id=%s" % surveyid)
	
class AddUser(webapp.RequestHandler):
	def post(self):
		user = users.get_current_user()
		raw_id = self.request.get('id')
		if raw_id :
			surveyid = int(raw_id)
			nickname = str(self.request.get('nickname'))
			if not nickname:
				self.redirect("/error?code=2")
			else :
				#check to ensure there is no previous entry
				check = AccessModel.gql("WHERE sid=:1 AND nick=:2",surveyid,nickname)
				#self.response.out.write(check.count())
				if check.count() != 0:
					self.redirect("/error?code=4")
				else :
					survey = SurveyModel.get_by_id(surveyid)
					#user has to be the author or admin
					if not authUser(user, survey.author) and not isAdmin(user) :
						self.redirect("/error?code=2")
					else :
						if survey.visibility == True:
							survey.visibility = False
							survey.put()
						access = AccessModel(sid=surveyid,
									nick=nickname)
						access.put()
						self.redirect("/perm?id=%s" % surveyid)
		else :
			self.redirect("/error?code=6")
	def get(self):
		self.redirect("/home")
		
class MakePublic(webapp.RequestHandler):
	def post(self):
		user = users.get_current_user()
		raw_id = self.request.get('id')
		if not raw_id:
			self.redirect("/error?code=2")
		else :
			surveyid = int(raw_id)
			survey = SurveyModel.get_by_id(surveyid)
			if user == survey.author or isAdmin(user) :
				#check to ensure there is no previous entry
				results = AccessModel.gql("WHERE sid=:1",surveyid)
				for result in results :
					result.delete()
				survey = SurveyModel.get_by_id(surveyid)
				survey.visibility = True
				survey.put()
				self.redirect("/perm?id=%s" % surveyid)
			else :
				self.redirect("/error?code=2")
	def get(self):
		self.redirect("/")

class ManagePermission(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		admin = "false"
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			if isAdmin(user):
				admin = "true"
				#self.response.out.write("Admin Interface")

		raw_id = self.request.get('id')
		if not raw_id:
			self.redirect("/error?code=2")
		else :
			surveyid = int(raw_id)
			survey = SurveyModel.get_by_id(surveyid)
			existingUsers = []
			if survey.visibility == True:
				visibility = "public"
			else :
				visibility = "limited"
				existingUsers = AccessModel.gql("WHERE sid=:1", surveyid)
	
			values = {'admin': admin,
				'visibility':visibility,
				'usernames' : existingUsers,
				'survey':survey,
	            'user':user,
	            'url':url,
	            'url_linktext':url_linktext				  
			}
			self.response.out.write(template.render('html/header.html', values))
			self.response.out.write(template.render('html/manageperm.html', values))
			self.response.out.write(template.render('html/footer.html', ""))

class ChangeSurvey(webapp.RequestHandler):
	def post(self):
		surveyid = int(self.request.get('surveyid'))
		survey = SurveyModel.get_by_id(surveyid)
		newsurvey_name = self.request.get('surveyname')
		raw_expiry = self.request.get('expiry')
		if raw_expiry:
			expiry = datetime.date(datetime.strptime(str(raw_expiry), '%Y-%m-%d'))
		else :
			expiry = datetime.date(datetime.strptime('2012-12-31', '%Y-%m-%d'))
		
		author = survey.author
		user = users.get_current_user()
		#check if no survey exists with same name for the author
		check = SurveyModel.gql("WHERE surveyname=:1 and author=:2 and expiry=:3", newsurvey_name, author,expiry)
		#self.response.out.write(check.count())
		if check.count() == 1:
			self.redirect("/error?code=1")
		elif author == user or isAdmin(user):
			survey.surveyname = newsurvey_name
			survey.expiry = expiry
			survey.put()
			#Updating Survey Questions
			questions = QuestionModel.gql("WHERE sid=:1 and author=:2", surveyid, author)
			for question in questions:
				question.surveyname = newsurvey_name
				question.put()
			self.redirect('/edit?' + urllib.urlencode({'id':surveyid }))
		else :
			self.redirect("/error?code=2")

class AddQuestion(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		admin = "false"
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			if isAdmin(user):
				admin = "true"
				#self.response.out.write("Admin Interface")
		if admin =="true":
			surveys = db.GqlQuery("Select * from SurveyModel")
		else :
			surveys = SurveyModel.gql("Where author=:1", user)	
		raw_id = self.request.get('id');
		survey = ""
		if raw_id :
			surveyid = int(raw_id)
			survey = SurveyModel.get_by_id(surveyid)

		values = {'admin': admin,
			'selsurvey': survey,
            'active': "addQ",
            'user':user,
            'url':url,
            'url_linktext':url_linktext,
            'surveys' : surveys
		}
		self.response.out.write(template.render('html/header.html', values))
		self.response.out.write(template.render('html/addq.html', values))
		self.response.out.write(template.render('html/footer.html', ""))
		
	def post(self):
		user = users.get_current_user()
		#surveys = SurveyModel.gql("Where author=:1",user)
		raw_id = str(self.request.get('surveyid'))
		
		surveyid = int(raw_id)
		if surveyid == -1:
			self.redirect('/error?code=3')
		else :
			survey = SurveyModel.get_by_id(surveyid)
			question = self.request.get('questiondes')
			raw_answers = self.request.get('answers')
			if not question or not raw_answers:
				self.redirect('/error?code=3')
			else :
				#Remove extra lines and spaces
				answerchoices = raw_answers.strip()
				answers = answerchoices.splitlines(0)
				anslist = []
				s = set()
				for ans in answers :
					if ans.strip() != ""  :
						if ans not in s:#No same answer choice twice	
							anslist.append(ans)
							s.add(ans)					
							
					
				if not authUser(user, survey.author) and not isAdmin(user):
					self.redirect('/error?code=2') 
				ques = QuestionModel(author=survey.author,
									sid=surveyid,
									nick = user.nickname(),
									surveyname=survey.surveyname,
										questiondes=question,
										answerlist=anslist)
				ques.put()
				self.redirect('/edit?' + urllib.urlencode({'id':surveyid }))
		
class UpdateQuestion(webapp.RequestHandler):
	def post(self):
		user = users.get_current_user()
		#surveys = SurveyModel.gql("Where author=:1",user)
		raw_id = self.request.get('surveyid');
		surveyid = int(raw_id)
		survey = SurveyModel.get_by_id(surveyid);
		question = self.request.get('questiondes')
		
		if not authUser(user, survey.author) and not isAdmin(user) :
			self.redirect("/error?code=2")
		else :
		#Remove extra lines and spaces
			answerchoices = self.request.get('answers').strip()
			answers = answerchoices.splitlines(0)
			anslist = []
			s = set()
			for ans in answers :
				if ans.strip() != "":	
					if ans not in s:#No same answer choice twice	
						anslist.append(ans)
						s.add(ans)	
			todo = str(self.request.get('todo'))
			
			if todo == "update":
				self.response.out.write(todo)
				questionid = int(self.request.get('questionid'))
				questionEntity = QuestionModel.get_by_id(questionid)
				questionEntity.answerlist = anslist
				questionEntity.questiondes = question
				questionEntity.put()
				#delete all voting details for modified questions
				votes = VoteModel.gql("WHERE qid=:1",questionid)
				for vote in votes:
					vote.delete()
				results = ResultModel.gql("WHERE qid=:1",questionid)
				for result in results:
					result.delete()
			else :
				ques = QuestionModel(author=survey.author,
									sid = surveyid,
									nick = user.nickname(),
									surveyname=survey.surveyname,
										questiondes=question,
										answerlist=answers)
				ques.put()
			self.redirect('/edit?' + urllib.urlencode({'id':surveyid }))

class ManageSurvey(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		admin = "false"
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			if isAdmin(user):
				admin = "true"
				#self.response.out.write("Admin Interface")
		if admin =="true":
			surveys = db.GqlQuery("Select * from SurveyModel ORDER BY created")
		else :
			surveys = SurveyModel.gql("Where author=:1 ORDER BY created", user)

		values = {'admin': admin,			
			'surveys': surveys,
            'active': "view",
            'user':user,
            'url':url,
            'url_linktext':url_linktext
		}
		self.response.out.write(template.render('html/header.html', values))
		self.response.out.write(template.render('html/view.html', values))
		self.response.out.write(template.render('html/footer.html', ""))

class Participate(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		admin = "false"
		surveys = []
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			if isAdmin(user):
				admin = "true"
				#self.response.out.write("Admin Interface")
			if admin == "true":
				surveys = db.GqlQuery("SELECT * FROM SurveyModel where expiry >=:1", date.today())
			else :
				surveys = SurveyModel.gql("where visibility=True and expiry >=:1", date.today())
			
			if admin == "false":
				queryAccess = AccessModel.gql("WHERE nick=:1",user.nickname())
				for result in queryAccess:
					survey = SurveyModel.get_by_id(result.sid)
					surveys.append(survey)
				
		values = {'admin': admin,
			'surveys': surveys,
            'active': "participate",
            'user':user,
            'url':url,
            'url_linktext':url_linktext
		}
		self.response.out.write(template.render('html/header.html', values))
		self.response.out.write(template.render('html/participate.html', values))
		self.response.out.write(template.render('html/footer.html', ""))

class ErrorHandle(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		admin = "false"
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			if isAdmin(user):
				admin = "true"
				#self.response.out.write("Admin Interface")

		surveys = SurveyModel.gql("Where author=:1", user)
		code = int(self.request.get('code'))

		values = {'admin': admin,
			'surveys': surveys,
			'code':code,
            'user':user,
            'url':url,
            'url_linktext':url_linktext
		}
		self.response.out.write(template.render('html/header.html', values))
		self.response.out.write(template.render('html/error.html', values))
		self.response.out.write(template.render('html/footer.html', ""))
	def post(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		admin = "false"
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			if isAdmin(user):
				admin = "true"
				#self.response.out.write("Admin Interface")

		surveys = SurveyModel.gql("Where author=:1", user)
		code = int(self.request.get('code'))

		values = {'admin': admin,
			'surveys': surveys,
			'code':code,
            'user':user,
            'url':url,
            'url_linktext':url_linktext
		}
		self.response.out.write(template.render('html/header.html', values))
		self.response.out.write(template.render('html/error.html', values))
		self.response.out.write(template.render('html/footer.html', ""))

class ViewVotes(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		admin = "false"
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			if isAdmin(user):
				admin = "true"
				#self.response.out.write("Admin Interface")

		qid = long(self.request.get('qid'))
		question = QuestionModel.get_by_id(qid)
		author = question.author
		surveyid = question.sid
		survey = SurveyModel.get_by_id(surveyid)
		if not authUser(user,author) and admin == "false" and user:
			self.redirect("/error?code=2")
		else :
			Voters = VoteModel.gql("WHERE qid=:1",qid)
			values = {'admin': admin,
				'voters': Voters,
				'question':question,
				'survey':survey,
	            'user':user,
	            'url':url,
	            'url_linktext':url_linktext
			}
			self.response.out.write(template.render('html/header.html', values))
			self.response.out.write(template.render('html/viewVotes.html', values))
			self.response.out.write(template.render('html/footer.html', ""))


class ResultHandler(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		admin = "false"
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			if isAdmin(user):
				admin = "true"
				#self.response.out.write("Admin Interface")

		raw_id= self.request.get('id')
		surveyid = int(raw_id)
		survey =  SurveyModel.get_by_id(surveyid)
		survey_name =survey.surveyname
		questions = QuestionModel.gql("WHERE sid=:1 ",surveyid)

		values = {'admin': admin,
            'user':user,
            'url':url,
            'url_linktext':url_linktext
		}
		self.response.out.write(template.render('html/header.html', values))
		if user :
			self.response.out.write("""<table align="center"  width="40%%" >
			<tr><th colspan="2" bgcolor="#0033FF"><font color="#FFF" >%s</font></th></tr>""" % survey_name)
			if survey.author == user or admin=="true":
				self.response.out.write("""<tr >
			<td colspan="6" align="center"><font color="red">Click on question name to view all the voters</font></th>
		</tr>""")
			for question in questions:
				answerlist = question.answerlist #All answer choices
				qid = long(question.key().id())
				questiondes = question.questiondes
				if question.author == user or admin=="true":
					
					self.response.out.write("""<tr><td colspan="2" bgcolor="#e5ecf9"><b><a href="viewVotes?qid=%s">%s</a></b></td></tr>""" % (qid,questiondes))
				else :
					self.response.out.write("""<tr><td colspan="2" bgcolor="#e5ecf9"><b>%s</b></td></tr>""" %questiondes)
				self.response.out.write("""<tr><td>Votes</td><td>Choices</td></tr>""")
				for ans  in answerlist:
					result = ResultModel.gql("WHERE answer=:1 AND qid=:2",ans,qid)
					if result.count() > 0:
						value = result.get().count
					else :
						value = 0
					self.response.out.write("""<tr><td>%s</td>""" %value)
					self.response.out.write("""<td>%s</td></tr>""" %ans)
				self.response.out.write("""<td colspan="2"><hr/></td></tr>""")
			self.response.out.write("""</table>""")
		self.response.out.write(template.render('html/footer.html', ""))


class StartSurvey(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		admin = "false"
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			if isAdmin(user):
				admin = "true"
				#self.response.out.write("Admin Interface")			
		raw_id = self.request.get('id')
		surveyid = int(raw_id)
		survey = SurveyModel.get_by_id(surveyid)
		author = survey.author
		nonVotedQ=[]
		votedQA = {}
		allQ = QuestionModel.gql("WHERE sid=:1 AND author=:2 ",surveyid,author)
		total = allQ.count()
		for question in allQ :
			qid = long(question.key().id())
			queryVote = VoteModel.gql("WHERE qid=:1 AND voter=:2",qid,user)
			if queryVote.count() == 0:#not voted yet
				nonVotedQ.append(question)
			else :
				votedQA[question]= queryVote.get().answer

		values = {'admin': admin,
			'surveyname' :survey.surveyname,
			'nonVotedQ':nonVotedQ,
			'votedQA': votedQA,
            'user':user,
            'url':url,
            'url_linktext':url_linktext,
            'id':surveyid,
            'total':total,
		}
		self.response.out.write(template.render('html/header.html', values))
		self.response.out.write(template.render('html/survey.html', values))
		self.response.out.write(template.render('html/footer.html', ""))
	
	def post(self):
		user = users.get_current_user()

		total = int(self.request.get('total'))+1
		raw_sid = self.request.get('id')
		if raw_sid :
			surveyid = int(raw_sid)
			for x in range(1,total):
				#update question Model entity
				self.response.out.write(x)
				raw_qid = self.request.get('qid'+str(x))
				qid = int(raw_qid)
				
				raw_answer = self.request.get('answer'+str(x))
				voter=user
				if raw_answer :
					#question = QuestionModel.get_by_id(qid)
					answer = str(raw_answer)				
					#confirm whether the voter is present or not
					confirm = VoteModel.gql("WHERE qid=:1 AND voter=:2",qid,user)
					self.response.out.write(str(confirm.count())+" where qid " + str(qid) + str(voter))
					if confirm.count() != 0:
						self.redirect("/error?code=5")
					else :
						voteEntity = VoteModel (qid=qid,
											sid=surveyid,
											voter=voter,
											answer=answer)
						voteEntity.put()
						oldEntity = ResultModel.gql("WHERE qid=:1 and answer=:2",qid,answer)
						if oldEntity.count()==0 :
							newEntity = ResultModel(count=1,
												sid=surveyid,
												qid=qid,
												answer=answer)
						else :
							newEntity = oldEntity.get()
							newEntity.count = newEntity.count+1
						newEntity.put()
						self.redirect('/participate')
		else :
			self.redirect("/error?code=2")
		

class PopularSurvey(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		admin = "false"
		sorted_list =[]
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
			if isAdmin(user):
				admin = "true"
				#self.response.out.write("Admin Interface")
		
			surveys = db.GqlQuery("SELECT * FROM SurveyModel")
			if admin == "true":
				surveys = db.GqlQuery("SELECT * FROM SurveyModel where expiry >=:1", date.today())
			else :
				surveys = SurveyModel.gql("where visibility=True and expiry >=:1", date.today())
				queryAccess = AccessModel.gql("WHERE nick=:1",user.nickname())
				for result in queryAccess:
					survey = SurveyModel.get_by_id(result.sid)
					surveys.append(survey)
	
			surveydict = {}
			
			for survey in surveys :
				s=set([])
				sid = long(survey.key().id())
				votes = VoteModel.gql("WHERE sid=:1",sid)
				for vote in votes :
					s.add(vote.voter)
				
				totalVotes = len(s)
				surveydict[survey]=totalVotes
	
			sorted_list = sorted(surveydict.iteritems(), key=operator.itemgetter(1))
		#self.response.out.write(surveydict)


		values = {'admin': admin,
			'active':"pop",
			'list':sorted_list,
            'user':user,
            'url':url,
            'url_linktext':url_linktext
		}
		self.response.out.write(template.render('html/header.html', values))
		self.response.out.write(template.render('html/popular.html', values))
		self.response.out.write(template.render('html/footer.html', ""))
		
application = webapp.WSGIApplication([('/', MainPage),
									('/popS', PopularSurvey),
									('/userM', UserManagement),
									('/addAdmin', AddAdmin),
									('/removeAdmin', RemoveAdmin),
									('/viewVotes', ViewVotes),
									('/makepublic', MakePublic),
									('/search', Search),
									('/results', ResultHandler),
									('/removeUser', RemoveUser),
									('/perm', ManagePermission),
									('/addUser', AddUser),
									('/vote', StartSurvey),
									('/castvote', StartSurvey),
									('/updateQ', UpdateQuestion),
									('/error', ErrorHandle),
									('/changeN', ChangeSurvey),
									('/deleteS', DeleteSurvey),
									('/deleteQ', DeleteQuestion),
									('/homepage', HomePage),
									('/home', MainPage),
									('/edit', EditSurvey),
									('/manageSurvey', ManageSurvey),
									('/create', CreateSurvey),
									('/addQ', AddQuestion),
									('/participate', Participate)],
									debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()
