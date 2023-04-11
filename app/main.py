__copyright__ = """
Copyright 2020, Cisco Systems, Inc. 
All Rights Reserved. 

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES 
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR 
OTHER DEALINGS IN THE SOFTWARE. 
"""

from flask import Flask, request, Response
from ldap3 import Server, Connection, NTLM, SUBTREE
import os
import sys

app = Flask(__name__)

pwd = os.getenv("PASSWORD")
user = os.getenv("LDAP_USER")
search_base = os.getenv("LDAP_SEARCH_BASE")
ldap_server = os.getenv("LDAP_SERVER")
ldap_port = int(os.getenv("LDAP_PORT"))
url = os.getenv("URL")
print(f"Server: {ldap_server}\nPort: {ldap_port}\nBase: {search_base}\nUser: {user}\nURL: {url}")

ldapserver = Server(ldap_server, port=ldap_port)
ldapconn = Connection(ldapserver, user=user, password=pwd, authentication=NTLM)
ldapconn.bind()


def ldap_search(to_search):
    ldap_filter_search = f"(&(objectCategory=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2))(|(displayName={to_search})(givenName={to_search})(sn={to_search})))"
    ldap_results_search = ldapconn.extend.standard.paged_search(search_base=search_base,
                                                                search_filter=ldap_filter_search,
                                                                search_scope=SUBTREE,
                                                                attributes=["displayName", "mail", "title"])
    return ldap_results_search


def ldap_get(the_user):
    ldap_filter_user = f"(&(objectCategory=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2))(|(mail={the_user})))"
    ldap_results_user = ldapconn.extend.standard.paged_search(search_base=search_base, search_filter=ldap_filter_user,
                                                              search_scope=SUBTREE,
                                                              attributes=["mail", "displayName", "telephoneNumber",
                                                                          "mobile"])
    return ldap_results_user


@app.route('/')
def home():
    xml = f"""
    <CiscoIPPhoneInput>
  <Title>Search the Directory</Title>
  <Prompt>Search:</Prompt>
  <URL>{url}/search</URL>
  <InputItem>
   <DisplayName>Search</DisplayName>
   <QueryStringParam>search</QueryStringParam>
   <DefaultValue></DefaultValue>
   <InputFlags>A</InputFlags>
  </InputItem>
</CiscoIPPhoneInput>
"""
    return Response(xml, mimetype='text/xml')


@app.route('/user')
def user():
    to_get = request.args.get('mail')
    get_user = ldap_get(to_get)
    my_data = []
    user_results = ""
    for blah in get_user:
        print(blah)
        try:
            if blah['type'] == "searchResRef":
                continue
        except:
            pass  # we should have user information.
        print("we have something")
        name = blah['attributes']['displayName']
        phone = blah['attributes']['telephoneNumber']
        mobile = blah['attributes']['mobile']
        my_data.append({"name": f"{name}", "phone": f"{phone}", "mobile": f"{mobile}"})
        user_results = user_results + f"""<MenuItem>
           <Name>Phone {phone}</Name>
           <URL>Dial:{phone}</URL>
          </MenuItem><MenuItem>
           <Name>Mobile {mobile}</Name>
           <URL>Dial:{mobile}</URL>
          </MenuItem>"""

    xml = f"""<CiscoIPPhoneMenu>
          <Title>Available Numbers to call</Title>
          <Prompt>Please select a number</Prompt>{user_results}</CiscoIPPhoneMenu>"""

    return Response(xml, mimetype='text/xml')


@app.route('/search')
def search():
    search_criteria = request.args.get('search')
    if not search_criteria:
        search_criteria = "*"
    else:
        search_criteria = "*" + request.args.get('search') + "*"
    print(search_criteria)
    get_ldap_search = ldap_search(search_criteria)
    my_data = []
    search_results = ""
    for blah in get_ldap_search:
        print(blah)
        try:
            if blah['type'] == "searchResRef":
                continue
        except:
            pass  # we should have user information.
        print("we have something")
        name = blah['attributes']['displayName']
        mail = blah['attributes']['mail']
        title = blah['attributes']['title']
        if not mail:
            print("User has no mail setting")
            continue
        my_data.append({"name": f"{name}", "mail": f"{mail}", "title": f"{title}"})
        search_results = search_results + f"""<MenuItem>
   <Name>{name}</Name>
   <URL>{url}/user?mail={mail}</URL>
  </MenuItem>"""

    xml = f"""<CiscoIPPhoneMenu>
  <Title>Search Results</Title>
  <Prompt>Please select a user</Prompt>{search_results}</CiscoIPPhoneMenu>"""

    return Response(xml, mimetype='text/xml')
