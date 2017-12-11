import peewee
PASSWORD = '.?K>b_Hj-T3{]Vc;'

# POST_KEYS = ['AcceptedAnswerId', 'Tags', 'Title', 'OwnerUserId', 'LastEditorDisplayName','Id', 'LastEditorUserId',
#              'OwnerDisplayName', 'ViewCount', 'LastEditDate','CommentCount', 'Body', 'CommunityOwnedDate','PostTypeId',
#              'AnswerCount','ClosedDate', 'Score', 'FavoriteCount','CreationDate', 'ParentId', 'LastActivityDate']

cnx = {
    'NAME': 'magic',
    'USER': 'magic',
    'PASSWORD': '.?K>b_Hj-T3{]Vc;',
    'HOST': 'magic.c83wppb36trw.us-east-1.rds.amazonaws.com'
}

db = peewee.MySQLDatabase(cnx['NAME'], host=cnx['HOST'], port=3306, user=cnx['USER'],
                          passwd=cnx['PASSWORD'])



class Tags(peewee.Model):
    Id = peewee.PrimaryKeyField()
    TagName = peewee.TextField()
    Count = peewee.IntegerField()
    ExcerptPostId = peewee.IntegerField()
    WikiPostId = peewee.IntegerField()
    class Meta:
        database = db

class PostLinks(peewee.Model):
    Id = peewee.PrimaryKeyField()
    PostId = peewee.IntegerField()
    RelatedPostId = peewee.IntegerField()
    LinkTypeId = peewee.IntegerField()
    CreationDate = peewee.DateTimeField(default = None, null = True)
    class Meta:
        database = db

class RelatedPostLinks(peewee.Model):
    PostId = peewee.IntegerField()
    RelatedPostId = peewee.IntegerField()
    LinkTypeId = peewee.IntegerField()
    class Meta:
        database = db


class QuestionPosts(peewee.Model):
    Id = peewee.PrimaryKeyField()
    Tags = peewee.TextField()
    Title = peewee.TextField()
    AcceptedAnswerId = peewee.IntegerField(default= None, null=True)
    OwnerUserId = peewee.IntegerField(default = None, null = True)
    OwnerDisplayName = peewee.TextField(default = None, null = True)
    ViewCount = peewee.IntegerField()
    CommentCount  = peewee.IntegerField(default= None, null= True)
    FavoriteCount = peewee.IntegerField()
    AnswerCount = peewee.IntegerField()
    Score = peewee.IntegerField(default=None)
    CreationDate = peewee.DateTimeField(default = None, null = True)
    TextBody = peewee.TextField(default=None, null=True)
    CodeBody = peewee.TextField(default=None, null = True)
    class Meta:
        database = db


class AnswerPosts(peewee.Model):
    Id = peewee.PrimaryKeyField()
    ParentId = peewee.IntegerField()
    CreationDate = peewee.DateTimeField(default = None, null = True)
    Score = peewee.IntegerField(default=None)
    OwnerUserId = peewee.IntegerField()
    CommentCount  = peewee.IntegerField(default= None, null= True)
    TextBody = peewee.TextField(default=None, null=True)
    CodeBody = peewee.TextField(default=None, null = True)
    class Meta:
        database = db


class Users(peewee.Model):
    Id = peewee.PrimaryKeyField()
    Reputation = peewee.IntegerField()
    DisplayName = peewee.TextField()
    UpVotes = peewee.IntegerField()
    DownVotes = peewee.IntegerField()
    class Meta:
        database = db




class SearchRun(peewee.Model):
    date_pulled = peewee.DateTimeField()
    class Meta:
        database = db



class SearchResult(peewee.Model):
    run = peewee.ForeignKeyField(SearchRun)
    page_num = peewee.IntegerField(default=None)
    url = peewee.TextField(default=None)
    s3_path = peewee.CharField(unique=True)
    question_header = peewee.TextField(default= None)
    tags = peewee.TextField(default = None)
    num_votes = peewee.IntegerField(default=None)
    num_answer = peewee.IntegerField(default= None)
    num_views = peewee.IntegerField(default=None)
    class Meta:
        database = db


class Questions(peewee.Model):
    question = peewee.PrimaryKeyField(SearchResult)
    code = peewee.TextField(default= None)
    text = peewee.TextField(default=None)
    favorite_count = peewee.IntegerField(default=None)

    class Meta:
        database = db


class Answers(peewee.Model):
    question = peewee.ForeignKeyField(SearchResult)
    code = peewee.TextField(default= None)
    text = peewee.TextField(default=None)
    vote_count = peewee.IntegerField(default=None)
    accepted = peewee.BooleanField(default=None)
    bounty_award = peewee.IntegerField(default=None)

    class Meta:
        database = db



class ConnectedQuestions(peewee.Model):
    question = peewee.ForeignKeyField(SearchResult)
    url = peewee.TextField(default=None)
    score = peewee.IntegerField(default=None)
    type = peewee.CharField(default=None)
    title = peewee.TextField(default=None)
    class Meta:
        database = db
