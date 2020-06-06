from atlassian import Jira

j = Jira(
    url='https://zazucli.atlassian.net/',
    username='nhwiles@gmail.com',
    password='ZdgU1Xtft8OoQu1ZFNu085D6')

me = j.issue('ZZ-5', fields='assignee')
print(me['key'])
try:
    j.assign_issue(me['key'], 'asdf')
except Exception as e:
    print(e)