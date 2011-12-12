import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.dist import use_library
use_library('django', '1.2')
import urllib
from google.appengine.ext import db, webapp
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
	sid = db.IntegerProperty(required=True)
	author = db.UserProperty(required=True)
	surveyname = db.StringProperty(required=True)
	questiondes = db.StringProperty(required=True)
	answerlist = db.StringListProperty(required=True)

# Todo defines the data model for the Todos
# as it extends db.model the content of the class will automatically stored
class VoteModel(db.Model):
	qid = db.IntegerProperty(required=True)
	voter = db.UserProperty(required=True)
	answer = db.StringProperty(required=True)

class ResultModel(db.Model):
	qid = db.IntegerProperty(required=True)
	answer = db.StringProperty(required=True)
	count = db.IntegerProperty(default=0)

	
class MainPage(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		
		surveys = db.GqlQuery("SELECT * FROM SurveyModel where author=:1", user)
		values = {
			'surveys':surveys,
            'active': "home",
            'user':user,
            'url':url,
            'url_linktext':url_linktext				  
		}
		
		self.response.out.write(template.render('html/header.html', values))
		self.response.out.write(template.render('html/home.html', values))
		self.response.out.write(template.render('html/footer.html', ""))
	

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
		self.response.out.write(template.render('html/header.html', values))
		self.response.out.write(template.render('html/create.html', values))
		self.response.out.write(template.render('html/footer.html', ""))
	
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
		survey = SurveyModel(author=user,
							surveyname=survey_name)
		survey.put()
		#check whether the survey name already exists or not
		self.response.out.write(template.render('html/header.html', values))
		self.response.out.write("The survey %s has been successfully created. Please view the survey to add questions" % survey_name)
		self.response.out.write(template.render('html/footer.html', ""))

class EditSurvey(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		surveyid = int(self.request.get('id'))
		survey = SurveyModel.get_by_id(surveyid)
		questions = db.GqlQuery("SELECT * FROM QuestionModel where sid =:1 and author=:2",
							surveyid, survey.author);
		values = {'survey':survey,
			'questions': questions,
            'active': "edit",
            'url':url,
            'user':user,
            'url_linktext':url_linktext	
		}
		self.response.out.write(template.render('html/header.html', values))
		self.response.out.write(template.render('html/edit.html', values))
		self.response.out.write(template.render('html/footer.html', ""))

class DeleteQuestion(webapp.RequestHandler):
	def post(self):
		questionid = int(self.request.get('questionid'))
		questionEntity = QuestionModel.get_by_id(questionid)
		if questionEntity.author == users.get_current_user() :
			votes = VoteModel.gql("WHERE qid=:1",questionid)
			for vote in votes:
				vote.delete()
			results = ResultModel.gql("WHERE qid=:1",questionid)
			for result in results:
				result.delete()
			questionEntity.delete()
			raw_id = self.request.get('surveyid');
			surveyid = int(raw_id)
			self.redirect('/edit?' + urllib.urlencode({'id':surveyid }))
		else :
			self.response.out.write("Unauthorized access!!!")
			self.redirect(self.request.uri)

class DeleteSurvey(webapp.RequestHandler):
	def get(self):
		surveyid = int(self.request.get('id'))
		survey = SurveyModel.get_by_id(surveyid)
		survey_name = survey.surveyname
		author = survey.author
		#Deleting Survey Questions
		questions = QuestionModel.gql("WHERE sid=:1 and author=:2", surveyid, author)
		for question in questions:
			votes = VoteModel.gql("WHERE qid=:1",question.key().id())
			for vote in votes:
				vote.delete()
			results = ResultModel.gql("WHERE qid=:1",question.key().id())
			for result in results:
				result.delete()
			question.delete()
		if (author == users.get_current_user()):
			survey.delete()
			self.redirect("/view")
		else :
			self.response.out.write("Unauthorized access!!!")
			self.redirect(self.request.uri)

class ChangeSurvey(webapp.RequestHandler):
	def post(self):
		surveyid = int(self.request.get('surveyid'))
		survey = SurveyModel.get_by_id(surveyid)
		newsurvey_name = self.request.get('surveyname')
		oldsurvey_name = survey.surveyname
		author = survey.author
		#check if no survey exists with same name for the author
		check = SurveyModel.gql("WHERE surveyname=:1 and author=:2", newsurvey_name, author)
		self.response.out.write(check.count())
		if check.count() == 1:
			self.redirect("/error?code=1")
		elif author == users.get_current_user():
			survey.surveyname = newsurvey_name
			survey.put()
			#Updating Survey Questions
			questions = QuestionModel.gql("WHERE sid=:1 and author=:2", surveyid, author)
			for question in questions:
				question.surveyname = newsurvey_name
				question.put()
			self.redirect('/edit?' + urllib.urlencode({'id':surveyid }))
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
		surveys = SurveyModel.gql("Where author=:1", user)	
		raw_id = self.request.get('id');
		survey = ""
		if raw_id :
			surveyid = int(raw_id)
			survey = SurveyModel.get_by_id(surveyid)
		
		values = {'selsurvey': survey,
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
		raw_id = self.request.get('surveyid')
		surveyid = int(raw_id)
		survey = SurveyModel.get_by_id(surveyid)
		question = self.request.get('questiondes')
				
		#Remove extra lines and spaces
		answerchoices = self.request.get('answers').strip()
		answers = answerchoices.splitlines(0)
		ques = QuestionModel(author=user,
							sid=surveyid,
							surveyname=survey.surveyname,
								questiondes=question,
								answerlist=answers)
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
			#delete all voting details
			"""votes = VoteModel.gql("WHERE qid=:1",questionid)
			for vote in votes:
				vote.delete()
			results = ResultModel.gql("WHERE qid=:1",questionid)
			for result in results:
				result.delete()
			question.delete()"""
		else :
			ques = QuestionModel(author=user,
								sid = surveyid,
								surveyname=survey.surveyname,
									questiondes=question,
									answerlist=answers)
			ques.put()
		self.redirect('/edit?' + urllib.urlencode({'id':surveyid }))

class ViewSurvey(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		surveys = SurveyModel.gql("Where author=:1 ORDER BY created", user)
		values = {'surveys': surveys,
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
		self.response.out.write(template.render('html/header.html', values))
		self.response.out.write(template.render('html/participate.html', values))
		self.response.out.write(template.render('html/footer.html', ""))

class ErrorHandle(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		surveys = SurveyModel.gql("Where author=:1", user)
		code = int(self.request.get('code'))
		values = {'surveys': surveys,
			'code':code,
            'user':user,
            'url':url,
            'url_linktext':url_linktext
		}
		self.response.out.write(template.render('html/header.html', values))
		self.response.out.write(template.render('html/error.html', values))
		self.response.out.write(template.render('html/footer.html', ""))

class ResultHandler(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		url = users.create_login_url(self.request.uri)
		url_linktext = 'Login'
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		raw_id= self.request.get('id')
		surveyid = int(raw_id)
		survey_name = SurveyModel.get_by_id(surveyid).surveyname
		questions = QuestionModel.gql("WHERE sid=:1 ",surveyid)
		values = {
            'user':user,
            'url':url,
            'url_linktext':url_linktext
		}
		self.response.out.write(template.render('html/header.html', values))
		self.response.out.write("""<table align="center"  width="40%%" >
		<tr><th colspan="2" bgcolor="#e5ecf9" >%s</th></tr>""" % survey_name)
		
		for question in questions:
			list = question.answerlist #All answer choices
			qid = long(question.key().id())
			questiondes = question.questiondes
			self.response.out.write("""<tr><td colspan="2"><b>%s</b></td></tr>""" %questiondes)
			self.response.out.write("""<tr><td>Votes</td><td>Choices</td></tr>""")
			for ans  in list:
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
		if user:
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'	
			
		raw_id = self.request.get('id')
		surveyid = int(raw_id)
		survey = SurveyModel.get_by_id(surveyid)
		author = survey.author
		
		#votedQ=[]
		nonVotedQ=[]
		#votedA=[]
		votedQA = {}
		allQ = QuestionModel.gql("WHERE sid=:1 AND author=:2 ",surveyid,author)
		total = allQ.count()
		for question in allQ :
			qid = long(question.key().id())
			#self.response.out.write("qid-"+str(qid)+","+user)
			queryVote = VoteModel.gql("WHERE qid=:1 AND voter=:2",qid,user)
			if queryVote.count() == 0:#not voted yet
				nonVotedQ.append(question)
			else :
				#votedQ.append(question)
				#votedA.append(queryVote.get().answer)
				votedQA[question]= queryVote.get().answer
				#self.response.out.write(votedQA)
		#votedQ = QuestionModel.gql("WHERE surveyname=:1 AND author=:2",survey.surveyname,author)
		self.response.out.write("non-"+str(nonVotedQ.__len__()))
		#self.response.out.write("voted"+str(votedQ.__len__()))
		values = {'nonVotedQ':nonVotedQ,
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
		#url = users.create_login_url(self.request.uri)
		#url_linktext = 'Login'
		#if user:
		#	url = users.create_logout_url(self.request.uri)
		#	url_linktext = 'Logout'	
			
		#raw_id = self.request.get('id')
		#surveyid = int(raw_id)
		#survey = SurveyModel.get_by_id(surveyid)
		
		total = int(self.request.get('total'))+1
		
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
					self.redirect("/error?code=3")
				
				voteEntity = VoteModel (qid=qid,
									voter=voter,
									answer=answer)
				voteEntity.put()
				oldEntity = ResultModel.gql("WHERE qid=:1 and answer=:2",qid,answer)
				if oldEntity.count()==0 :
					newEntity = ResultModel(count=1,
										qid=qid,
										answer=answer)
				else :
					newEntity = oldEntity.get()
					newEntity.count = newEntity.count+1
				newEntity.put()
		self.redirect('/participate')

application = webapp.WSGIApplication([('/', MainPage),
									('/results', ResultHandler),
									('/vote', StartSurvey),
									('/castvote', StartSurvey),
									('/updateQ', UpdateQuestion),
									('/error', ErrorHandle),
									('/changeN', ChangeSurvey),
									('/deleteS', DeleteSurvey),
									('/deleteQ', DeleteQuestion),
									('/home', MainPage),
									('/edit', EditSurvey),
									('/view', ViewSurvey),
									('/create', CreateSurvey),
									('/addQ', AddQuestion),
									('/participate', Participate)],
									debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()
