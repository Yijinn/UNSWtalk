#!/web/cs2041/bin/python3.6.3

# written by andrewt@cse.unsw.edu.au October 2017
# as a starting point for COMP[29]041 assignment 2
# https://cgi.cse.unsw.edu.au/~cs2041/assignments/UNSWtalk/

import os,re,glob,collections
from datetime import datetime
from flask import Flask, render_template, session, request, url_for, redirect, send_from_directory

students_dir = "dataset-medium";

app = Flask(__name__)

'''
get_students() returns students_info
students_info data structure: students_info[z5119672]={zid:z5119672
                                      name:yijin zheng
                                      friends: [z5000000, z5111111]
                                      etc....
                                     }


get_posts returns posts
an example for posts data strucure: 
posts[static/dataset/z5119672/0.txt]={'who':z5119672
                                      'time':time read from file
                                      'message':i like comp2041
                                      'comments'[0]:{'who':z5119672
                                                     'time': time read from file
                                                     'message':i dont like comp2041
                                                     'replies'[0]:{'who': z5119672
                                                                   'time': read from file
                                                                   'message': if i get a hd then i like comp2041
                                                                  }
                                                    }
                                     }

'''

@app.route('/', methods=['GET','POST'])
@app.route('/login', methods=['POST', 'GET'])
def login():
#Basically every function strat with following lines by defending user get into page by typing http addrress
#But in login function. if session has had an zid, and login page was opened. Then maybe this page was opened by another user
#So clear the session up for the new user to login
    user = session.get('user')
    if user:
        session.pop('user', None)
        return redirect(url_for('login'))

    zid = request.form.get('zid', '')
    password = request.form.get('password', '')


    if zid:
        students = get_students()
        if zid in students:
            if password == students[zid]['password']:
                session['user'] = zid
                return redirect(url_for('profile'))
            else:
                return render_template('login.html', error="Wrong password")	
        else:
            return render_template('login.html', error="unknown zid")
    else:
        return render_template('login.html')


#User's home page
@app.route('/profile', methods=['GET','POST'])
def profile():
    zid = session.get('user')
    if not zid:
        return redirect(url_for('login'))
#students_info and posts data structure was explained at top
    students_info = get_students()
    posts = get_posts(zid)
    return render_template('profile.html', students_info=students_info, posts=posts, student=zid)
    

#Other people pages
@app.route('/friends/<zid>', methods=['POST', 'GET'])
def otherProfile(zid):
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
#If users click themselves on others' friends list then gome back to thier home page
    if user == zid:
        return redirect(url_for('profile'))

    students_info = get_students()
    posts = get_posts(zid)
#If this person is in user friend list friendShip=1 else 0
    friendShip=0
    if zid in students_info[user]['friends']:
        friendShip = 1
    return render_template('student.html', students_info=students_info, user=user, student=zid, posts=posts, friendShip=friendShip)

#Search friends page
@app.route('/searchFriend', methods=['POST'])
def searchFriend():
    zid = session.get('user')
    if not zid:
        return redirect(url_for('login'))

# Ignore cases and if found append into searchList[]
    keyword = request.form.get('searchFor')
    searchList=[]
    students_info=get_students()
    if keyword:
        for i in students_info.keys():
            find = re.search(keyword, students_info[i]['name'], flags=re.IGNORECASE)
            if find:
                searchList.append(students_info[i]['zid'])
    if searchList != None:
        return render_template('searchFriend.html', student=zid, searchList=searchList, keyword=keyword, students_info=students_info)
    else:
        return render_template('searchFriend.html', student=zid, keyword=keyword, students_info=students_info)

@app.route('/posting', methods=['POST', 'GET'])
def posting():

    user = session.get('user')
    if not user:
        return redirect(url_for('login'))

    postText = request.form.get('post')
    students_info = get_students()
    posts = get_posts(user)
#We don't want to make a new post if user just click post without any typing
    if postText:
        count = 0
        for i in posts.keys():
            if int(i.split('/')[-1].replace('.txt', '')) > count:
                count = int(i.split('/')[-1].replace('.txt', ''))
        count = count+1
        with open('static/'+ students_dir + '/' + user + '/' + str(count) + '.txt', 'w') as f:
            f.write("from: " + user +'\n')
            time = str(datetime.now())
            time = re.sub(r".\d+$", "", time)
            time = re.sub(r" ", "T", time)
            f.write("time: " + time + '+0000'+'\n')
            f.write("message: " + postText +'\n')
#Write a new file. The name of the file will be the greatest number in that directory in case overwrite some exsting files
#Then go back to homepage and reload posts
    return redirect(url_for('profile'))        

@app.route('/searchPost', methods=['POST'])
def searchPost():

    user = session.get('user')
    if not user:
        return redirect(url_for('login'))

    students_info = get_students()
    
    keyword = request.form.get('searchPost')
    posts = {}
#Again we don't want to search if user just click search without typing anything
    if keyword:
        list = glob.glob('static/'+ students_dir + "/*"+"/*.txt")
        posts_list=[]
        for i in list:
#We are only looking for \d.txt without any '-' between and open all the \d.txt the re.search every message line by keyword
#If we find that keyword addFlag goes to 1
            add_flag=0
            post = re.match(r"^\d+.txt$", i.split('/')[-1])
            if post:
                with open(i) as f:
                    who=""
                    time=""
                    context=""
                    for line in f.readlines():
                        searchTime = re.search(r"^time: (.*)", line)
                        searchWho = re.search(r'^from: (.*)', line)
                        message = re.search(r"^message: (.*)", line)
                        if searchTime:
                            time = searchTime.group(1)
                            time = time.replace("+0000", "")
                            time = re.sub(r"T", " ", time)
                        if searchWho:
                            who = searchWho.group(1)
                        if message:
                            match = re.search(keyword, message.group(1), flags=re.IGNORECASE)
                            if match:
                                context = message.group(1)
                                add_flag = 1
            if add_flag == 1:
                comments = get_comments(i)
                posts[i] = {'who':who,
                            'time':time,
                            'message':context,
                            'comments':comments}
    return render_template('searchPost.html', students_info=students_info, posts=posts, student=user, keyword=keyword)

@app.route('/comment/<zid>', methods=['POST', 'GET'])
def comment(zid):

    user = session.get('user')
    if not user:
        return redirect(url_for('login'))

    students_info = get_students()
    posts = get_posts(user)
    commentText = request.form.get('comment')
#path is hidden input value in html path will be a post path e.g z5119672/0.txt
#and re.sub '0.txt' to '-' then collection all z5119672/0-\d.txt
    path = request.form.get('path')
    list=[]
    comments_list=[]
    if commentText:
        path = re.sub(r".txt$", "-", path)
        list = glob.glob(path+"*")
        for i in list:
            if re.search(r"^\d+-\d+.txt$", i.split('/')[-1]):
                comments_list.append(i)
        count=0
        for i in comments_list:
            count+=1
        count+=1
        with open(path + str(count) + '.txt', 'w') as f:
            f.write("from: " + user +'\n')
            time = str(datetime.now())
            time = re.sub(r".\d+$", "", time)
            time = re.sub(r" ", "T", time)
            f.write("time: " + time + '+0000'+'\n')
            f.write("message: " + commentText +'\n')
    if user == zid:
        return redirect(url_for('profile'))
    else:
        return redirect(url_for('otherProfile', zid=zid))

@app.route('/reply/<zid>', methods=['POST','GET'])
def reply(zid):

    user = session.get('user')
    if not user:
        return redirect(url_for('login'))

    students_info = get_students()
    posts = get_posts(user)
    replyText = request.form.get('reply')
#hidden input value again
    path = request.form.get('path')
    commentNumber = request.form.get('commentNumber')
    list=[]
    reply_list=[]
    if replyText:
        path = re.sub(r".txt$", "-", path)
        path = path + str(commentNumber)+'-'
        list = glob.glob(path+"*")
        for i in list:
            if re.search(r"^\d+-\d+-\d+.txt$", i.split('/')[-1]):
                reply_list.append(i)
        count=0
        for i in reply_list:
            count+=1
        count+=1
        with open(path + str(count) + '.txt', 'w') as f:
            f.write("from: " + user +'\n')
            time = str(datetime.now())
            time = re.sub(r".\d+$", "", time)
            time = re.sub(r" ", "T", time)
            f.write("time: " + time + '+0000'+'\n')
            f.write("message: " + replyText +'\n')
    if user == zid:
        return redirect(url_for('profile'))
    else:
        return redirect(url_for('otherProfile', zid=zid))
#Read student.txt into f. modify 'friends: 'line then overwrite into student.txt
@app.route('/unfriend/<zid>', methods=['POST'])
def unfriend(zid):

    user = session.get('user')
    if not user:
        return redirect(url_for('login'))

    students_info = get_students()
    path = 'static/' + students_dir + '/' + user + '/student.txt'
    newContext=[]
    with open(path, 'r') as f:
        context = f.readlines()
    for line in context:
        match = re.match("^friends: (.*)", line)
        if match:
            line = re.sub(r"[()]", "", line)
            line = re.sub(', *'+zid, '', line)
            line = line.replace(zid, '')
            line = line.replace(zid,'')
        newContext.append(line)
    with open(path, 'w') as f:
        f.writelines(newContext)
    return redirect(url_for('otherProfile', zid=zid))

@app.route('/addfriend/<zid>', methods=['POST'])
def addfriend(zid):
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))

    students_info = get_students()
    path = 'static/' + students_dir + '/' + user + '/student.txt'
    newContext=[]
    with open(path, 'r') as f:
        context = f.readlines()
    for line in context:
        match = re.match("^friends: (.*)", line)
        if match:
            line = re.sub(r"[()]", "", line)
            line = line.strip()
#maybe the user doesn't have any friends, then we want add the first friend without ',' at the end
            if re.search(r'.+', match.group(1)):
                line = line + ', ' + zid +'\n'
            else:
                line = line + zid + '\n'
        newContext.append(line)
    with open(path, 'w') as f:
        f.writelines(newContext)
    return redirect(url_for('otherProfile', zid=zid))



@app.route('/logout', methods=['POST'])
def logout():
#If haven't logged in, go to login page
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))

    session.pop('user', None)
    return redirect(url_for('login'))

#data structure explaination at the top
def get_students():
    students = collections.OrderedDict()
    list = sorted(glob.glob('static/' + students_dir + "/*"))
    for i in list:
        zid = i.split('/')
        students[zid[-1]] = {'zid': zid[-1]}
        if os.path.isfile('static/' + students_dir+"/"+zid[-1]+"/img.jpg"):
            students[zid[-1]]['image'] = url_for('static', filename=students_dir+"/"+zid[-1]+"/img.jpg")
        with open(i + '/student.txt') as f:
            for line in f.readlines():
                match = re.match(r"^(\w+): (.*)$", line)
                if match.group(1) == "password":
                    students[zid[-1]]['password'] = match.group(2)
                if match.group(1) == "full_name":
                    students[zid[-1]]['name'] = match.group(2)
                if match.group(1) == "friends":
                    friends = re.sub(r" ", "", match.group(2))
                    friends = re.sub(r"[()]", "", friends)
                    students[zid[-1]]['friends'] = friends.split(',')
                if match.group(1) == "program":
                    students[zid[-1]]['program'] = match.group(2)
                if match.group(1) == "birthday":
                    students[zid[-1]]['birthday'] = match.group(2)

    return students

def get_posts(zid):
    students_info = get_students()
    posts = collections.OrderedDict()
    list = glob.glob('static/'+ students_dir + "/*"+"/*.txt")
    posts_list=[]
    for i in list:
        if i.split('/')[-2] == zid:
            post = re.match(r"^\d+.txt$", i.split('/')[-1])
            if post:
                with open(i) as f:
                    for line in f.readlines():
                        time = re.match(r"^time: (.*)", line)
                        if time:
                            time = time.group(1)
                            time = time.replace("+0000", "")
                            time = re.sub(r"\D", "-", time)
                            time = datetime.strptime(time, '%Y-%m-%d-%H-%M-%S')
                            posts_list.append([i, time])
        else:
            post = re.match(r"^\d+.txt$", i.split('/')[-1])
            if post:
                with open(i) as f:
                    for line in f.readlines():
                        reference = re.match(zid, line)
                        if reference: break;
                    for line in f.readlines():
                        time = re.match(r"^time: (.*)$")
                        if time:
                            time = time.group(1)
                            time = time.replace("+0000", "")
                            time = re.sub(r"\D", "-", time)
                            time = datetime.strptime(time, '%Y-%m-%d-%H-%M-%S')
                            posts_list.append([i, time])
#An example of posts_list;
#posts_list = [['static/z5119672/0.txt', 2017-10-30T00:00:00], ['static/z5119672.1.txt', 2018-12-30T00:00:00]]
#Then sort by time, Then put them into posts ordered dictionary
    posts_list = sorted(posts_list, reverse=True, key=lambda x:x[1])

    for i in posts_list:
        with open(i[0]) as f:
            for line in f.readlines():
                who = re.match(r"^from: (.*)", line)
                if who:
                    who = who.group(1)
                    break
        with open(i[0]) as f:
            context=""
            for line in f.readlines():
                match = re.match("^message: (.*)$", line)
                if match:
                    context= match.group(1)
                    replaceList = re.findall(r"z\d{7}", context)
                    for replace in replaceList:
                        if replace in students_info.keys():
                            context = context.replace(replace, students_info[replace]['name'])
        comments = get_comments(i[0])
        if comments:
            posts[i[0]] = {'time':i[1]}
            posts[i[0]]['who'] = who
            posts[i[0]]['message']=context
            posts[i[0]]['comments'] = comments
        else:
            posts[i[0]] = {'time':i[1]}
            posts[i[0]]['who'] = who
            posts[i[0]]['message']=context
    return posts

#data structure expaination at the top
def get_comments(path):
    students_info = get_students()
    comments={}
    comments_list=[]
    path = path.replace('.txt', '*')
    list = glob.glob(path)
    for i in list:
        match = re.search(r"^\d+-(\d+).txt$", i.split('/')[-1])
        if match:
            comments_list.append([int(match.group(1)),i])
    comments_list = sorted(comments_list, key= lambda x: x[0])
    for i in comments_list:
        with open(i[1]) as f:
            context=""
            for line in f.readlines():
                searchWho = re.search(r"^from: (.*)", line)
                searchTime = re.search(r"^time: (.*)", line)
                match = re.search("^message: (.*)$", line)
                if searchWho:
                    who = searchWho.group(1)
                if searchTime:
                    time = searchTime.group(1)
                    time = time.replace('+0000', '')
                    time = re.sub(r"\D", "-", time)
                    time = datetime.strptime(time, '%Y-%m-%d-%H-%M-%S')
                if match:
                    context= match.group(1)
                    replaceList = re.findall(r"z\d{7}", context)
                    for replace in replaceList:
                        if replace in students_info.keys():
                            context = context.replace(replace, students_info[replace]['name'])

        replies = get_replies(i[1])
        if replies:
            comments[i[0]] = {'who':who,
                         'message':context,
                          'time': time,
                          'replies':replies}
        else:
            comments[i[0]] = {'who':who,
                         'time': time,
                         'message':context}
    return comments

#data structure expaination at the top
def get_replies(path):
    students_info = get_students()
    replies={}
    reply_list=[]
    path = path.replace('.txt', '-*')
    list = glob.glob(path)
    for i in list:
        match = re.search(r"^\d+-\d+-(\d+).txt$", i.split('/')[-1])
        if match:
            reply_list.append([int(match.group(1)), i])
    reply_list = sorted(reply_list, key= lambda x: x[0])
    for i in reply_list:
        with open(i[1]) as f:
            context=""
            for line in f.readlines():
                searchWho = re.search(r"^from: (.*)", line)
                searchTime = re.search(r"^time: (.*)", line)
                match = re.search("^message: (.*)$", line)
                if searchWho:
                    who = searchWho.group(1)
                if searchTime:
                    time = searchTime.group(1)
                    time = time.replace('+0000', '')
                    time = re.sub(r"\D", "-", time)
                    time = datetime.strptime(time, '%Y-%m-%d-%H-%M-%S')
                if match:
                    context= match.group(1)
                    replaceList = re.findall(r"z\d{7}", context)
                    for replace in replaceList:
                        if replace in students_info.keys():
                            context = context.replace(replace, students_info[replace]['name'])

        replies[i[0]]={'who':who, 'message':context, 'time':time};
    return replies



if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True)
