import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.dist import use_library
use_library('django', '1.2')

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
	updated = db.DateTimeProperty(auto_now=True)

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
		self.response.out.write("%s" %surveys.get().author)
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
		self.response.out.write("The survey name is %s" %survey_name)
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
		self.response.out.write("%s" %questions.get())
		self.response.out.write(template.render('html/footer.html',""))

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
		id = int(raw_id)
		survey = SurveyModel.get_by_id(id);
		values = {'selsurvey': survey,
            'active': "edit",
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
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		surveys = SurveyModel.gql("Where author=:1",user)
		raw_id = self.request.get('surveyid');
		id = int(raw_id)
		survey = SurveyModel.get_by_id(id);
		question = self.request.get('questiondes')
		#Remove extra lines and spaces
		answerchoices = self.request.get('answers').strip()
		answers = answerchoices.splitlines()
		ques = QuestionModel(author=user,
							surveyname = survey.surveyname,
								questiondes = question,
								answerlist = answers)
		ques.put()
		self.response.out.write(ques.surveyname)
		self.redirect("/edit?id=%s" %id)

class ViewSurvey(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		surveys = SurveyModel.gql("Where author=:1",user)
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
		surveys = SurveyModel.gql("Where author=:1",user)
		values = {'surveys': surveys,
            'active': "view",
            'user':user,
            'url':url,
            'url_linktext':url_linktext
		}
		self.response.out.write(template.render('html/header.html',values))
		self.response.out.write(template.render('html/view.html',values))
		self.response.out.write(template.render('html/footer.html',""))
		
application = webapp.WSGIApplication([('/',MainPage),
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