#
# Collective Knowledge
#
# See CK LICENSE.txt for licensing details
# See CK Copyright.txt for copyright details
#
# Developer: Grigori Fursin
#

cfg={}  # Will be updated by CK (meta description of this module)
work={} # Will be updated by CK (temporal data)
ck=None # Will be updated by CK (initialized CK kernel) 

# Local settings

import os

##############################################################################
# Initialize module

def init(i):
    """
    Input:  {}

    Output: {
              return   - return code =  0, if successful
                                     >  0, if error
              (error)  - error text if return > 0
            }

    """
    return {'return':0}

##############################################################################
# Create repository in a given directory and record info in CK

def add(i):
    """
    Note, that we can't create repos in parallel (recording to repo cache may fail).
    However, for now, we do not expect such cases (i.e. repos are created rarely)

    Input:  {
              (repo_uoa)               - repo UOA (where to create entry)
              uoa                      - data UOA
              (uid)                    - data UID (if uoa is an alias)
              (name)                   - user friendly data name

              (cids[0])                - as uoa or full CID

              (path)                   - if =='' - get current path
              (use_default_path)       - if 'yes' create repository in the default path (CK_REPOS)
                                         instead of the current path

              (default)                - if 'yes', no path is used, 
                                         but the repository is taken either 
                                         from the CK directory or from CK_LOCAL_REPO

              (remote)                 - if 'yes', remote repository
              (remote_repo_uoa)        - if !='' and type=='remote' repository UOA on the remote CK server

              (shared)                 - if not remote and =='git', shared through GIT

              (url)                    - if type=='remote' or 'git', URL of remote repository or git repository
              (sync)                   - if 'yes' and type=='git', sync repo after each write operation
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }

    """

    o=i.get('out','')

    a=i.get('repo_uoa','')
    d=i.get('data_uoa','')
    di=i.get('data_uid','')
    dn=i.get('data_name','')

    remote=i.get('remote','')
    rruoa=i.get('remote_repo_uoa','')
    shared=i.get('shared','')
    url=i.get('url','')
    sync=i.get('sync','')
    df=i.get('default','')

    udp=i.get('use_default_path','')

    # Get path
    p=i.get('path','')
    if p=='': p=os.getcwd()

    # Normalize path
    p=os.path.normpath(p)

    if udp=='yes': p=os.path.join(ck.work['dir_repos'], d)

    # If console mode, first, check if shared (GIT, etc)
    if o=='con':
       # Asking for alias
       if df!='yes' and (d=='' or ck.is_uid(d)):
          r=ck.inp({'text':'Enter an alias for this repository (or nothing to generate UID): '})
          d=r['string']
          if d=='': d=di
          if d=='':
             r=ck.gen_uid({})
             if r['return']>0: return r
             di=r['uid']
             d=di

       # Asking for a user-friendly name
       if df!='yes' and dn=='':
          r=ck.inp({'text':'Enter a user-friendly name of this repository (or nothing to reuse alias): '})
          dn=r['string']
          if dn=='': dn=d

       # Asking for a user-friendly name
       if df!='yes' and udp=='':
          r=ck.inp({'text':'Would you like to create repo in the current path ("yes" or "no"/Enter for CK_REPOS): '})
          cur_path=r['string']
          if cur_path!='yes': p=os.path.join(ck.work['dir_repos'], d)

       # Asking if remote
       if df!='yes' and remote=='':
          r=ck.inp({'text':'Is this repository a remote CK web service ("yes" or "no"/Enter)? '})
          remote=r['string'].lower()
          if remote!='yes': remote=''

       # Asking for remote url
       if df!='yes' and remote=='yes' and url=='':
          r=ck.inp({'text':'Enter URL of remote CK repo (http://localhost:3344/json?): '})
          url=r['string'].lower()
          if url=='':
             return {'return':1, 'error':'URL is empty'}

       # Asking for remote repo UOA
       if df!='yes' and remote=='yes' and rruoa=='':
          r=ck.inp({'text':'Enter remote repo UOA or Enter for nothing: '})
          rruoa=r['string'].lower()

       # Asking for shared
       if remote=='' and shared=='':
          r=ck.inp({'text':'Is this repository shared ("git" or "no"/Enter)? '})
          shared=r['string'].lower()
          if shared!='git': shared=''

       # Check additional parameters if git
       if shared=='git' and url=='':
          s='Enter URL of GIT repo '
          durl='https://github.com/ctuning/'+d+'.git'
          if d=='': s+='(for example, https://github.com/ctuning/ck-analytics.git)'
          else:     s+='(or Enter for '+durl+')'
          r=ck.inp({'text': s+': '})
          url=r['string'].lower()
          if url=='': url=durl
                              
       # Check additional parameters if git
       if shared=='git' and sync=='':
          r=ck.inp({'text': 'Would you like to sync repo each time after writing to it ("yes" or "no"/Enter)?: '})
          sync=r['string'].lower()

    # Check if already registered (if not remote)
    if remote!='yes':
       r=ck.find_repo_by_path({'path':p})
       if r['return']>0 and r['return']!=16: 
          return r

    # Check if repository is already registered with this path
    r=ck.find_repo_by_path({'path':p})
    if r['return']==0:
       return {'return':1, 'error':'repository with a given path is already registered in CK'}
    elif r['return']!=16: 
       return r

    # Prepare local description file
    py=os.path.join(p,ck.cfg['repo_file'])

    # Create dummy if doesn't exist
    if not os.path.isdir(p):
       os.makedirs(p)

    # If git, clone repo
    if shared=='git':
       r=pull({'path':p, 'type':shared, 'url':url, 'clone':'yes', 'out':o})
       if r['return']>0: return r

       # Check if there is a local repo description
       if os.path.isfile(py):
          r=ck.load_json_file({'json_file':py})
          if r['return']>0: return r
          dc=r['dict']

          xd=dc.get('data_uoa','')
          xdi=dc.get('data_uid','')
          xdn=dc.get('data_name','')

          if o=='con':
             ck.out('Cloned repository has the following info:')
             ck.out(' UID                = '+xdi)
             ck.out(' UOA                = '+xd)
             ck.out(' User friendly name = '+xdn)
             r=ck.inp({'text': 'Would you like to reuse them ("yes" or "no"/Enter)?: '})
             reuse=r['string'].lower()
             if reuse=='yes': 
                d=xd
                di=xdi
                dn=xdn

    # Prepare meta description
    dd={}
    if df=='yes': dd['default']='yes'
    if remote=='yes': 
       dd['remote']='yes'
       if rruoa!='': 
          dd['remote_repo_uoa']=rruoa
    if shared!='':
       dd['shared']=shared
       if sync!='': 
          dd['sync']=sync
    if url!='': dd['url']=url
    dd['path']=p

    # If not default, go to common core function to create entry
    if df!='yes':
       ii={'module_uoa':work['self_module_uoa'],
           'action':'add',
           'data_uoa':d,
           'dict':dd,
           'common_func':'yes'}
       if a!='': ii['repo_uoa']=a
       if di!='': ii['data_uid']=di
       if dn!='': ii['data_name']=dn
       rx=ck.access(ii)
       if rx['return']>0: return rx
    else:
       # Load default repo and prepare return
       ii={'module_uoa':work['self_module_uoa'],
           'action':'load',
           'data_uoa':'default',
           'common_func':'yes'}
       rx=ck.access(ii)
    px=rx['path']
    dx=rx['data_uid']
    alias=rx['data_alias']

    # Update repo cache if not default local
    dz={'data_uoa':d, 'data_uid':dx, 'data_alias':alias, 'path_to_repo_desc':px, 'data_name':dn, 'dict':dd}

    if df!='yes':
       r=ck.reload_repo_cache({}) # Ignore errors
       ck.cache_repo_uoa[d]=dx
       ck.cache_repo_info[dx]=dz
       r=ck.save_repo_cache({})
       if r['return']>0: return r

    # Record local info of the repo (just in case)
    if 'path_to_repo_desc' in dz: del (dz['path_to_repo_desc'])        # Avoid recording some local info
    if dz.get('dict',{}).get('path','')!='': del (dz['dict']['path'])  # Avoid recording some local info
    if not os.path.isfile(py):
       ry=ck.save_json_to_file({'json_file':py, 'dict':dz})
       if ry['return']>0: return ry

    # If sync, add it ...

    # If console mode, print various info
    if o=='con':
       ck.out('')
       ck.out('CK repository successfully registered!')
       ck.out('')

       if df=='yes':
          ck.out('Please, do not forget to add path to this repository to CK_LOCAL_REPO environment variable:')
          ck.out('')
          ck.out('  Linux: export CK_LOCAL_REPO='+p)
          ck.out('  Windows: set CK_LOCAL_REPO='+p)
       else:
          ck.out('CK repo description path = '+px)
          ck.out('CK repo UID              = '+dx)

    return rx

##############################################################################
# Pull from remote repo if URL

def pull(i):
    """
    Input:  {
              (path)  - repo UOA (where to create entry)
              (type)  - type
              (url)   - URL

                or

              (uoa)   - repo UOA

              (clone) - if 'yes', clone repo instead of update
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }

    """

    o=i.get('out','')

    p=i.get('path','')
    t=i.get('type','')
    url=i.get('url','')

    uoa=i.get('data_uoa','')
    cids=i.get('cids',[])
    if len(cids)>0: uoa=cids[0]

    if uoa!='':
       # Loading repo
       r=ck.access({'action':'load',
                    'module_uoa':work['self_module_uoa'],
                    'data_uoa':uoa,
                    'common':'yes'})
       if r['return']>0: return r
       d=r['dict']

       p=d['path']
       t=d['type']
       url=d.get('url','')

    # Updating ...
    if t=='git':
       tt='update'
       if i.get('clone','')=='yes': tt='clone'

       px=os.getcwd()
       if not os.path.isdir(p):
          os.makedirs(p)

       os.chdir(p)

       s=ck.cfg['repo_types'][t][tt].replace('$#url#$', url).replace('$#path#$', p)
       
       if o=='con':
          ck.out('')
          ck.out('Executing command: '+s)
          ck.out('')

       r=os.system(s)

       if o=='con': 
          ck.out('')

       os.chdir(px) # Restore path

       if r>0:
          return {'return':1, 'error':'repository update likely failed - exit code '+str(r)}
    else:
       if o=='con':
          ck.out('CK warning: this repository is not shared!')

    return {'return':0}

##############################################################################
# Create repository in a given directory and record info in CK

def create(i):
    """
    See function 'add'

    """

    return add(i)

##############################################################################
# Recache all repositories in cache

def recache(i):
    """
    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }
    """




    return {'return':0}

##############################################################################
# Remove information about repository

def rm(i):
    """
    Input:  {
              (repo_uoa) - repo UOA (where to delete entry about repository)
              uoa        - data UOA
              (force)    - if 'yes', force removal
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }
    """

    global cache_repo_uoa, cache_repo_info, paths_repos_all, cache_repo_init

    ruoa=i.get('repo_uoa','')
    uoa=i.get('data_uoa','')

    o=i.get('out','')

    if uoa=='': 
       return {'return':1, 'error':'UOA of the repository is not defined'}

    r=ck.access({'action':'load',
                 'repo_uoa':ruoa,
                 'module_uoa':work['self_module_uoa'],
                 'data_uoa':uoa,
                 'common_func':'yes'})
    if r['return']>0: return r
    duid=r['data_uid']
    duoa=r['data_uoa']

    to_delete=True
    if o=='con' and i.get('force','')!='yes':
       r=ck.inp({'text':'Are you sure to delete information about repository '+duoa+' (Y/yes or N/no/Enter): '})
       c=r['string'].lower()
       if c!='y' and c!='yes': to_delete=False

    if to_delete:
       if o=='con': 
          ck.out('')
          ck.out('Reloading repo cache ...')
       r=ck.reload_repo_cache({}) # Ignore errors
       if r['return']>0: return r

       if o=='con': ck.out('Removing from cache ...')
       if duoa in ck.cache_repo_uoa: del (ck.cache_repo_uoa[duoa])
       if duid in ck.cache_repo_info: del (ck.cache_repo_info[duid])

       if o=='con': ck.out('Rewriting repo cache ...')
       r=ck.save_repo_cache({})
       if r['return']>0: return r

       if o=='con': ck.out('Removing entry ...')
       r=ck.access({'action':'remove',
                    'repo_uoa':ruoa,
                    'module_uoa':work['self_module_uoa'],
                    'data_uoa':uoa,
                    'common_func':'yes'})
       if r['return']>0: return r

       if o=='con': 
          ck.out('')
          ck.out('Information about repository was removed successfully!')
          ck.out('Note: repository itself was not removed!')

    return {'return':0}

##############################################################################
# Remove information about repository

def remove(i):
    """
    Input:  { See 'rm' function }
    Output: { See 'rm' function }
    """

    return rm(i)

##############################################################################
# Remove information about repository

def delete(i):
    """
    Input:  { See 'rm' function }
    Output: { See 'rm' function }
    """

    return rm(i)