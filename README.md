#Zazu (at your service)

Zazu is a CLI development workflow management tool that combines elements of git flow with CI and issue tracking.

[//]: # (http://graphviz.herokuapp.com/?token=4be881f64a929c1799830c1432830f30)
![alt text](http://vignette1.wikia.nocookie.net/disney/images/c/ca/Zazu01cf.png/revision/latest?cb=20120429182840 "Zazu") ![alt text](http://graphviz.herokuapp.com/?file=4be881f64a929c1799830c1432830f30.dot.png)

Zazu is a [Click](http://click.pocoo.org/5/) based CLI and is implemented in Python. If you're wondering why Click, this is a well [answered](http://click.pocoo.org/5/why/) question.

##Install
`pip install --upgrade --trusted-host pypi.lily.technology --index-url http://pypi.lily.technology:8080/simple zazu`

##Command overview
[//]: # (http://graphviz.herokuapp.com/?token=52f183defd40d8186202b2027291e59b)
![alt text](http://graphviz.herokuapp.com/?file=52f183defd40d8186202b2027291e59b.dot.png)

Note: dashed lines are not yet implemented

##Repo management 
- `zazu repo clone <name>` clones repo from github and installs GIT hooks (Unimplemented)
- `zazu repo init <name>` initializes repo to default project structure (Unimplemented)
- `zazu repo setup all` runs all of the setup steps below
	- `zazu repo setup hooks` installs default GIT hooks to the repo
	- `zazu repo setup ci` sets up CI builds based on the zazu.yaml file in the repo

###CI build configuration management
Zazu can setup CI server builds (currently only TeamCity is supported) to build targets specified by a recipe file (the zazu.yaml file in the root of a repo).

- `zazu repo setup ci`

##Development workflow management
- `zazu dev start` interactivly creates new JIRA ticket
- `zazu dev start <name>` e.g. `zazu dev start LC-440_a_cool_feature`
- `zazu dev status` displays ticket and pull request status
- `zazu dev ticket` launches web browser to the ticket page
- `zazu dev builds` launches web browser to the CI project page
- `zazu dev review` launches web browser to create/view a pull request


##Building
Zazu uses the zazu.yaml file to build goals defined there

- `zazu build --arch=x86_64-linux-gcc package`

##Build tool instalation
Zazu will automatically try to obtain required build tools needed for each target as specified in the zazu.yaml file. These may be installed/uninstalled manually as well:

- `zazu tool install <tool==version>`
- `zazu tool uninstall <tool==version>`

These tools will be installed to the `~/.bob/tools/` folder.


##zazu.yaml file
The zazu.yaml file lives at the base of the repo and describes the CI goals and architechures to be run. In addition it describes the requirements for each goal.
	

	components:
	  - name: networkInterface
	    goals:
	      - name: coverage
	        description: "Runs the \"check\" target and reports coverage via gcovr"
	        buildType: coverage
	        buildVars:
	              LOCAL_SERVER: ON
	        builds:
	          - arch: x86_64-linux-gcc
	      - name: package
	        buildType: minSizeRel          
	        builds:
	          - arch: arm32-linux-gnueabihf
	            requires:
	              bob:
	                - gcc-linaro-arm-linux-gnueabihf==4.9
	          - arch: x86_64-linux-gcc



###Compiler tuples
Architechures are defined as tupple in the folowing form:
`<ISA>-<OS>-<ABI>`
####Examples
- x86\_64-linux-gcc
- x86\_32-linux-gcc
- x86\_64-win-msvc_2013
- x86\_64-win-msvc_2015
- x86\_32-win-msvc_2013
- x86\_32-win-msvc_2015
- arm32-linux-gnueabihf
- arm32-none-eabihf