import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.dist import use_library
use_library('django', '1.2')
import urllib
from google.appengine.ext import db,webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users	

# Todo defines the data model for the Todos
# as it extends db.model the content of the class will automatically stored
class SurveyModel(db.Model):
	author = db.UserProperty(required=True)
	surveyname = db.StringProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)

# Todo defines the data model for the Todos
# as it extends db.model the content of the class will automatically stored
class QuestionModel(db.Model):
	author = db.UserProperty(required=True)
	surveyname = db.StringProperty(required=True)
	questiondes = db.StringProperty(required=True)
	answerlist = db.StringListProperty(required=True)
# Todo defines the data model for the Todos
# as it extends db.model the content of the class will automatically stored
class AnswerModel(db.Model):
	surveyname = db.StringProperty(required=True)
	question = db.StringProperty(required=True)
	

class MainPage(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		
		surveys = db.GqlQuery("SELECT * FROM SurveyModel where author=:1",user)
		values = {
			'surveys':surveys,
            'active': "home",
            'user':user,
            'url':url,
            'url_linktext':url_linktext				  
		}
		
		self.response.out.write(template.render('html/header.html',values))
		self.response.out.write(template.render('html/home.html',values))
		self.response.out.write(template.render('html/footer.html',""))
	

class CreateSurvey(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		values = {
            'active': "create",
            'user':user,
            'url':url,
            'url_linktext':url_linktext	
		}
		self.response.out.write(template.render('html/header.html',values))
		self.response.out.write(template.render('html/create.html',values))
		self.response.out.write(template.render('html/footer.html',""))
	
	def post(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		values = {
            'active': "create",
            'user':user,
            'url':url,
            'url_linktext':url_linktext	
		}
		survey_name = self.request.get('survey_name')
		survey = SurveyModel(author = user,
							surveyname = survey_name)
		survey.put()
		#check whether the survey name already exists or not
		self.response.out.write(template.render('html/header.html',values))
		self.response.out.write("The survey %s has been successfully created. Please view the survey to add questions" %survey_name)
		self.response.out.write(template.render('html/footer.html',""))

class EditSurvey(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		id = int(self.request.get('id'));
		survey = SurveyModel.get_by_id(id);
		questions = db.GqlQuery("SELECT * FROM QuestionModel where surveyname =:1 and author=:2",
							survey.surveyname,survey.author);
		values = {'survey':survey,
			'questions': questions,
            'active': "edit",
            'url':url,
            'user':user,
            'url_linktext':url_linktext	
		}
		self.response.out.write(template.render('html/header.html',values))
		self.response.out.write(template.render('html/edit.html',values))
		self.response.out.write(template.render('html/footer.html',""))

class DeleteQuestion(webapp.RequestHandler):
	def post(self):
		todo = self.request.get('todo');
		questionid = int(self.request.get('questionid'))
		questionEntity = QuestionModel.get_by_id(questionid)
		if questionEntity.author == users.get_current_user() :
			questionEntity.delete()
			raw_id = self.request.get('surveyid');
			id = int(raw_id)
			self.redirect('/edit?' + urllib.urlencode({'id':id }))
		else :
			self.response.out.write("Unauthorized access!!!")
			self.redirect(self.request.uri)

class DeleteSurvey(webapp.RequestHandler):
	def get(self):
		todo = self.request.get('todo');
		id = int(self.request.get('id'))
		survey = SurveyModel.get_by_id(id)
		survey_name = survey.surveyname
		author = survey.author
		#Deleting Survey Questions
		questions = QuestionModel.gql("WHERE surveyname=:1 and author=:2",survey_name,author)
		for question in questions:
			question.delete()
		if (author == users.get_current_user()):
			survey.delete()
			self.redirect("/view" )
		else :
			self.response.out.write("Unauthorized access!!!")
			self.redirect(self.request.uri)

class ChangeSurvey(webapp.RequestHandler):
	def post(self):
		id = int(self.request.get('surveyid'))
		survey = SurveyModel.get_by_id(id)
		newsurvey_name = self.request.get('surveyname')
		oldsurvey_name = survey.surveyname
		author = survey.author
		#check if no survey exists with same name for the author
		check = SurveyModel.gql("WHERE surveyname=:1 and author=:2",newsurvey_name,author)
		self.response.out.write(check.count())
		if check.count() == 1:
			self.redirect("/error?code=1")
		elif author == users.get_current_user():
			survey.surveyname = newsurvey_name
			survey.put()
			#Updating Survey Questions
			questions = QuestionModel.gql("WHERE surveyname=:1 and author=:2",oldsurvey_name,author)
			for question in questions:
				question.surveyname = newsurvey_name
				question.put()
			self.redirect('/edit?' + urllib.urlencode({'id':id }))
		else :
			self.response.out.write("Unauthorized access!!!")
			self.redirect(self.request.uri)

class AddQuestion(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		surveys = SurveyModel.gql("Where author=:1",user)	
		raw_id = self.request.get('id');
		survey = ""
		if raw_id :
			id = int(raw_id)
			survey = SurveyModel.get_by_id(id);
		
		values = {'selsurvey': survey,
            'active': "addQ",
            'user':user,
            'url':url,
            'url_linktext':url_linktext,
            'surveys' : surveys
		}
		self.response.out.write(template.render('html/header.html',values))
		self.response.out.write(template.render('html/addq.html',values))
		self.response.out.write(template.render('html/footer.html',""))
		
	def post(self):
		user = users.get_current_user()
		#surveys = SurveyModel.gql("Where author=:1",user)
		raw_id = self.request.get('surveyid');
		id = int(raw_id)
		survey = SurveyModel.get_by_id(id);
		question = self.request.get('questiondes')
				
		#Remove extra lines and spaces
		answerchoices = self.request.get('answers').strip()
		answers = answerchoices.splitlines(0)
		ques = QuestionModel(author=user,
							surveyname = survey.surveyname,
								questiondes = question,
								answerlist = answers)
		ques.put()
		self.redirect('/edit?' + urllib.urlencode({'id':id }))
		
class UpdateQuestion(webapp.RequestHandler):
	def post(self):
		user = users.get_current_user()
		#surveys = SurveyModel.gql("Where author=:1",user)
		raw_id = self.request.get('surveyid');
		id = int(raw_id)
		survey = SurveyModel.get_by_id(id);
		question = self.request.get('questiondes')
				
		#Remove extra lines and spaces
		answerchoices = self.request.get('answers').strip()
		answers = answerchoices.splitlines(0)
		todo = str(self.request.get('todo'))
		
		if todo == "update":
			self.response.out.write(todo)
			questionid = int(self.request.get('questionid'))
			questionEntity = QuestionModel.get_by_id(questionid)
			questionEntity.answerlist = answers
			questionEntity.questiondes = question
			questionEntity.put()
		else :
			ques = QuestionModel(author=user,
								surveyname = survey.surveyname,
									questiondes = question,
									answerlist = answers)
			ques.put()
		self.redirect('/edit?' + urllib.urlencode({'id':id }))

class ViewSurvey(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		surveys = SurveyModel.gql("Where author=:1 ORDER BY created",user)
		values = {'surveys': surveys,
            'active': "view",
            'user':user,
            'url':url,
            'url_linktext':url_linktext
		}
		self.response.out.write(template.render('html/header.html',values))
		self.response.out.write(template.render('html/view.html',values))
		self.response.out.write(template.render('html/footer.html',""))

class Participate(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		surveys = db.GqlQuery("SELECT * FROM SurveyModel")
		values = {'surveys': surveys,
            'active': "participate",
            'user':user,
            'url':url,
            'url_linktext':url_linktext
		}
		self.response.out.write(template.render('html/header.html',values))
		self.response.out.write(template.render('html/participate.html',values))
		self.response.out.write(template.render('html/footer.html',""))

class ErrorHandle(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		surveys = SurveyModel.gql("Where author=:1",user)
		code = int(self.request.get('code'))
		values = {'surveys': surveys,
			'code':code,
            'user':user,
            'url':url,
            'url_linktext':url_linktext
		}
		self.response.out.write(template.render('html/header.html',values))
		self.response.out.write(template.render('html/error.html',values))
		self.response.out.write(template.render('html/footer.html',""))
		
application = webapp.WSGIApplication([('/',MainPage),
									('/updateQ',UpdateQuestion),
									('/error',ErrorHandle),
									('/changeN',ChangeSurvey),
									('/deleteS',DeleteSurvey),
									('/deleteQ',DeleteQuestion),
									('/home',MainPage),
									('/edit',EditSurvey),
									('/view',ViewSurvey),
									('/create',CreateSurvey),
									('/addQ',AddQuestion),
									('/participate',Participate)],
									debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()