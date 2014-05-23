import jss

jp = jss.JSSPrefs()
j = jss.JSS(jp)
#p = jss.Policy(j)
ps = j.Policy()
p = j.Policy(97)

#with open('doc/policy_template.xml') as f:
#    a = f.read()
#
#new_policy = j.Policy(a)