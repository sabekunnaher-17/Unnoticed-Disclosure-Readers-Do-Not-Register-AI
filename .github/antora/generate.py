"""Original, project-specific SVG workflow illustrations in Antora's green theme.

No external resources, JavaScript, fonts or image-service dependencies. Each scene
has a separately composed mobile version and two animation-free alternatives.
"""
from html import escape
from pathlib import Path

THEME = {'bg': '#081510', 'panel': '#10231c', 'edge': '#285c43',
         'green': '#53f7ad', 'teal': '#73ddd0', 'text': '#edfff5', 'muted': '#adcbbb'}
META = {
    'projectflow': ('ProjectFlow', 'Tasks, people and deadlines in one workspace',
                    'C# / ASP.NET Core / EF Core / SQL Server', 'PLAN / ASSIGN / BUILD / REVIEW'),
    'hospital': ('Hospital Appointments', 'A collaborative appointment-booking workflow',
                 'PHP MVC / MySQL / JavaScript', 'DOCTOR / SLOT / BOOKING / DASHBOARD'),
    'billiard': ('Q-Billiard Shop', 'A desktop shop for billiard equipment',
                 'Java / Swing / AWT / File handling', 'BROWSE / CUSTOMIZE / PAYMENT UI / RECORDS'),
    'solar': ('Solar System Simulation', 'Orbits, camera perspectives and lighting',
              'C++ / OpenGL / GLUT', 'ORBITS / PERSPECTIVES / GRAPHICS'),
    'research': ('Unnoticed Disclosure', 'From survey responses to reported findings',
                 'Python / pandas / SciPy / scikit-learn', 'SCREEN / ANALYZE / VALIDATE / REPORT'),
    'portfolio': ('Sabekunnaher Antora', 'Projects, research and the person behind the code',
                  'React / TypeScript / Vite / GitHub Pages', 'BUILD / NAVIGATE / EXPLORE / CONNECT'),
    'calendar': ('Contribution Calendar Art', 'Decorative cells with disclosed backdated author dates',
                 'Python / Git / SVG', 'SYNTHETIC ART / NOT HISTORICAL DEVELOPMENT'),
    'profile': ('Sabekunnaher Antora', 'Full-stack development / Testing / Research',
                'C# / ASP.NET Core / EF Core / SQL Server / Java', 'CSE STUDENT AT AIUB / DHAKA, BANGLADESH'),
}


def t(x, y, value, size=18, color='muted', weight=400, anchor=None):
    a = f' text-anchor="{anchor}"' if anchor else ''
    color = THEME.get(color, color)
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}"{a}>{escape(str(value))}</text>'


def box(x, y, w, h, fill='panel', stroke='edge', radius=14):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{THEME.get(fill,fill)}" stroke="{THEME.get(stroke,stroke)}"/>'


class Scene:
    def __init__(self, slug, mobile=False, still=False):
        self.slug, self.mobile, self.still = slug, mobile, still
        self.w, self.h = (600, 780) if mobile else (1200, 550)
        if slug == 'profile':
            self.h = 800 if mobile else 540

    def packet(self, path, duration=8, phase=0, radius=4, color='green', fallback=(40,40)):
        color = THEME.get(color,color)
        if self.still:
            return f'<circle cx="{fallback[0]}" cy="{fallback[1]}" r="{radius}" fill="{color}"/>'
        return f'''<g class="moving"><circle r="{radius+5}" fill="{color}" opacity=".11"><animateMotion path="{path}" dur="{duration}s" begin="-{phase}s" repeatCount="indefinite"/></circle><circle r="{radius}" fill="{color}"><animateMotion path="{path}" dur="{duration}s" begin="-{phase}s" repeatCount="indefinite"/></circle></g><circle class="rest" cx="{fallback[0]}" cy="{fallback[1]}" r="{radius}" fill="{color}"/>'''

    def floating(self, content, x, y):
        transform = '' if self.still else '<animateTransform attributeName="transform" type="translate" values="0 -5;0 5;0 -5" dur="5s" repeatCount="indefinite"/>'
        return f'<g transform="translate({x} {y})"><g>{transform}{content}</g></g>'

    def task_token(self, path, fallback):
        card=box(-30,-12,60,24,'#17472d','green',6)+'<path d="M-19 -4H15M-19 4H6" stroke="#b3f27b" stroke-width="3" stroke-linecap="round"/>'
        if self.still:
            return f'<g transform="translate({fallback[0]} {fallback[1]})">{card}</g>'
        return f'<g class="moving">{card}<animateMotion path="{path}" dur="11s" repeatCount="indefinite"/></g><g class="rest" transform="translate({fallback[0]} {fallback[1]})">{card}</g>'

    def background(self):
        w,h=self.w,self.h
        s = f'''<defs><linearGradient id="background"><stop stop-color="#06100c"/><stop offset="1" stop-color="#102b1e"/></linearGradient><radialGradient id="halo"><stop stop-color="#53f7ad" stop-opacity=".15"/><stop offset="1" stop-color="#53f7ad" stop-opacity="0"/></radialGradient><pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" stroke="#53f7ad" stroke-opacity=".045" fill="none"/></pattern><clipPath id="frame"><rect x="2" y="2" width="{w-4}" height="{h-4}" rx="20"/></clipPath></defs>
<g clip-path="url(#frame)"><rect width="{w}" height="{h}" fill="url(#background)"/><ellipse cx="{w*.8}" cy="{h*.25}" rx="420" ry="320" fill="url(#halo)"/><rect width="{w}" height="{h}" fill="url(#grid)"/>'''
        for i in range(4):
            x=w-44-i*21
            words=''.join(t(x,j*27,word,11,'green') for j,word in enumerate(['01','{}','10','//','01','</>','10','::']))
            motion='' if self.still else f'<animateTransform attributeName="transform" type="translate" from="0 -240" to="0 {h+30}" dur="{14+i*2}s" begin="-{i*4}s" repeatCount="indefinite"/>'
            s += f'<g opacity=".13">{motion}{words}</g>'
        s+='</g>'
        s+=f'<rect x="2" y="2" width="{w-4}" height="{h-4}" rx="20" fill="none" stroke="#285c43"/>'
        border=f'M22 10H{w-22}Q{w-10} 10 {w-10} 22V{h-22}Q{w-10} {h-10} {w-22} {h-10}H22Q10 {h-10} 10 {h-22}V22Q10 10 22 10Z'
        s+=self.packet(border,22,0,3,fallback=(self.w-28,10))
        s+=self.packet(border,22,11,3,'teal',fallback=(28,self.h-10))
        return s

    def companion(self):
        # A small code companion: bobbing shell, antenna and two illuminated eyes.
        s='<path d="M0 -19V-28" stroke="#73ddd0"/><circle cy="-30" r="3" fill="#53f7ad"/>'
        s+=box(-24,-18,48,36,'panel','green',11)
        s+='<rect x="-13" y="-5" width="7" height="8" rx="2" fill="#53f7ad"/><rect x="6" y="-5" width="7" height="8" rx="2" fill="#73ddd0"/><path d="M-7 10H7" stroke="#53f7ad"/>'
        return self.floating(s,self.w-50,55)

    def standard_head(self):
        title,sub,stack,footer=META[self.slug]
        s=t(30,41,'ANTORA / '+('ORGANIZATION PROJECT' if self.slug=='hospital' else 'PROJECT WORKSPACE'),13,'green',600)
        if self.mobile:
            titles={'solar':['Solar System','Simulation'],'calendar':['Contribution','Calendar Art'],'hospital':['Hospital','Appointments']}
            lines=titles.get(self.slug,[title])
            for i,line in enumerate(lines):s+=t(30,98+i*40,line,33,'text',700)
            y=142+(len(lines)-1)*40
            subtitles={
                'calendar':['Decorative cells; deliberately','backdated author dates.'],
                'hospital':['A collaborative appointment','booking workflow.'],
                'research':['Survey responses, analysis','and reported findings.'],
                'portfolio':['Projects, research and the','person behind the code.']}
            for j,line in enumerate(subtitles.get(self.slug,[sub])):s+=t(30,y+j*26,line,18)
        else:
            s+=t(32,101,title,40,'text',700)+t(34,137,sub,21)
        return s+self.companion()

    def footer(self):
        title,sub,stack,label=META[self.slug]
        if self.mobile:
            # Technology strings deliberately wrap at fixed semantic boundaries.
            lines={
                'projectflow':['C# / ASP.NET Core','EF Core / SQL Server'],
                'hospital':['PHP MVC / MySQL','HTML / CSS / JavaScript'],
                'billiard':['Java / Swing / AWT','File handling'],
                'solar':['C++ / OpenGL / GLUT'],
                'research':['Python / pandas / SciPy','scikit-learn / Matplotlib'],
                'portfolio':['React / TypeScript','Vite / GitHub Pages'],
                'calendar':['Python / Git / SVG'],
            }[self.slug]
            s=f'<path d="M30 650H570" stroke="#285c43"/>'
            for i,line in enumerate(lines):s+=t(30,681+i*25,line,18,'green')
            s+=t(30,753,'ILLUSTRATIVE WORKFLOW / NOT LIVE DATA',12)
        else:
            s=t(32,465,label,17,'green',600)
            s+='<path d="M32 480H1168" stroke="#285c43"/>'
            s+=t(32,512,stack,17)+t(1167,535,'ILLUSTRATION / NOT LIVE TELEMETRY',11,anchor='end')
        return s

    def flow(self, labels, details):
        if self.mobile:
            s=''
            for i,(label,detail) in enumerate(zip(labels,details)):
                y=240+i*94
                s+=box(34,y,532,76)+t(55,y+29,f'0{i+1} / '+label,20,'green',600)+t(55,y+55,detail,16)
                if i<3:
                    s+=f'<path d="M300 {y+76}V{y+94}" stroke="#285c43" stroke-width="2"/>'
                    s+=self.packet(f'M300 {y+76}V{y+94}',3,i*.6,3,fallback=(300,y+85))
            return s
        s=''
        for i,(label,detail) in enumerate(zip(labels,details)):
            x=32+i*294
            s+=box(x,197,254,168)
            s+=t(x+20,232,f'0{i+1}',13,'teal',600)+t(x+20,281,label,24,'text',600)+t(x+20,320,detail,16)
            if i<3:
                s+=f'<path d="M{x+254} 281H{x+294}" stroke="#285c43" stroke-width="2"/>'
                s+=self.packet(f'M{x+254} 281H{x+294}',3,i*.6,4,fallback=(x+274,281))
        return s

    def kanban(self):
        if self.mobile:
            s=self.flow(['Plan','Assign','In progress','Review'],['Organize the workspace','Connect people and tasks','Move work through stages','Discuss, test and deliver'])
            path='M515 270V551'
            return s+self.task_token(path,(515,459))
        s=''
        for i,label in enumerate(['TO DO','IN PROGRESS','REVIEW']):
            x=32+i*392;s+=box(x,174,352,248)+t(x+20,207,label,16,'green',600)
            for j in range(2):
                y=233+j*76
                s+=box(x+18,y,316,58,'#153625','edge',9)
                s+=f'<circle cx="{x+37}" cy="{y+19}" r="4" fill="#73ddd0"/>'
                s+=f'<path d="M{x+52} {y+19}H{x+192}M{x+35} {y+38}H{x+256}" stroke="#426c56" stroke-width="5" stroke-linecap="round"/>'
        # A task token travelling between the board's stages, not a real issue.
        s+=self.task_token('M75 389H1120',(600,389))
        return s

    def solar(self):
        w=self.w;cx=w/2;cy=416 if self.mobile else 293
        s=box(30,234 if self.mobile else 171,w-60,384 if self.mobile else 251)
        s+=f'<circle cx="{cx}" cy="{cy}" r="40" fill="#53f7ad" opacity=".1"/><circle cx="{cx}" cy="{cy}" r="21" fill="#b3f27b"/>'
        for i,(rx,ry) in enumerate([(80,33),(151,68),(232 if self.mobile else 350,119 if self.mobile else 103)]):
            path=f'M{cx-rx} {cy}a{rx} {ry} 0 1 0 {2*rx} 0a{rx} {ry} 0 1 0 {-2*rx} 0'
            s+=f'<path d="{path}" fill="none" stroke="#285c43" stroke-width="1.7"/>'
            s+=self.packet(path,9+i*7,i*3,5+i*2,['green','teal','text'][i],fallback=(cx+rx,cy))
        s+=t(50,601 if self.mobile else 402,'ORBITAL MOTION / SCHEMATIC',12,'muted')
        return s

    def research(self):
        if self.mobile:
            return self.flow(['Screen','Analyze','Validate','Report'],['Prepare eligible responses','Explore the research questions','Cross-validation of models','Read the recorded findings'])
        s=self.flow(['Screen','Analyze','Validate','Report'],['Eligible responses','Python analysis','Cross-validation','Recorded findings'])
        s+='<path d="M58 390C180 390 160 374 280 377S450 406 590 388S810 372 935 387S1060 401 1140 380" fill="none" stroke="#53f7ad" stroke-width="2" opacity=".6"/>'
        s+=self.packet('M58 390C180 390 160 374 280 377S450 406 590 388S810 372 935 387S1060 401 1140 380',12,0,4,'teal',fallback=(590,388))
        return s

    def portfolio(self):
        x,y,w,h=(32,226,536,395) if self.mobile else (32,173,1136,247)
        s=box(x,y,w,h)+f'<path d="M{x} {y+37}H{x+w}" stroke="#285c43"/>'
        for i,c in enumerate(['green','teal','muted']):s+=f'<circle cx="{x+19+i*18}" cy="{y+19}" r="4" fill="{THEME[c]}"/>'
        s+=t(x+85,y+25,'antora / portfolio',13)
        navw=115 if self.mobile else 170
        s+=box(x+13,y+51,navw,h-65,'#0c1b14','edge',8)
        for i,label in enumerate(['About','Projects','Research','Contact']):s+=t(x+26,y+89+i*42,label,14 if self.mobile else 17,'green' if i==1 else 'muted')
        cw=w-navw-51;rx=x+navw+28
        s+=t(rx,y+86,'SELECTED WORK',13,'teal',600)
        for i in range(3):
            yy=y+104+i*(79 if self.mobile else 39)
            s+=box(rx,yy,cw,66 if self.mobile else 29,'#153625','edge',7)
            s+=f'<path d="M{rx+14} {yy+15}H{rx+cw-25}" stroke="#4e8a66" stroke-width="4" stroke-linecap="round"/>'
        path=f'M{rx+cw-12} {y+99}V{y+h-22}'
        return s+self.packet(path,8,0,4,'green',fallback=(rx+cw-12,y+150))

    def calendar(self):
        x0,y0=(45,277) if self.mobile else (98,205)
        cols,rows=(12,7) if self.mobile else (28,5)
        size,gap=(33,10) if self.mobile else (25,12)
        s=box(30,232 if self.mobile else 172,self.w-60,389 if self.mobile else 250)
        for r in range(rows):
            for c in range(cols):
                x,y=x0+c*(size+gap),y0+r*(size+gap)
                color=['#18462f','#23784a','#32aa69','#53d994'][(r+c)%4]
                s+=f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="5" fill="{color}"/>'
        s+=self.packet(f'M{x0} {y0-12}H{x0+(cols-1)*(size+gap)+size}',10,0,4,'teal',fallback=(x0+180,y0-12))
        s+=t(48,603 if self.mobile else 400,'SYNTHETIC CELLS / NOT WORK HISTORY',13,'text',600)
        return s

    def profile(self):
        s=t(32,44,'ANTORA / DEVELOPER WORKSPACE',13,'green',600)
        s+=self.companion()
        if self.mobile:
            s+=t(32,101,'Sabekunnaher',38,'text',700)+t(32,145,'Antora',38,'text',700)
            s+=t(32,191,'Full-stack development',23,'teal')+t(32,223,'Software testing / Research',20)
            x,y,w,h=32,263,536,271
            base=304
        else:
            s+=t(36,112,'Sabekunnaher Antora',46,'text',700)
            s+=t(38,159,'Full-stack development',26,'teal')+t(38,197,'Software testing / Research',22)
            s+=t(38,252,'Secure applications.',22)+t(38,286,'Tested workflows. Useful data.',22)
            x,y,w,h=656,190,510,236
            base=229
        s+=box(x,y,w,h)+t(x+22,base,'profile.cs',15,'green',600)
        code=[('education','CSE @ AIUB'),('focus','ASP.NET Core + SQL Server'),('quality','unit / integration / E2E'),('research','Python + team leadership')]
        for i,(key,val) in enumerate(code):
            s+=t(x+22,base+39+i*41,key+' :',17 if self.mobile else 15,'teal',600)
            s+=t(x+143,base+39+i*41,val,17 if self.mobile else 14,'text')
        if self.mobile:
            s+=t(32,585,'C# / ASP.NET Core / EF Core',18,'green')+t(32,616,'SQL Server / Java',18,'green')
            s+=t(32,696,'AIUB / DHAKA, BANGLADESH',17)
            s+=t(32,754,'BUILD / VERIFY / COLLABORATE',15,'green',600)
        else:
            s+=t(38,359,'C# / ASP.NET Core / EF Core',19,'green')+t(38,391,'SQL Server / Java',19,'green')
            s+=t(38,480,'CSE STUDENT AT AIUB / DHAKA, BANGLADESH',16)
        return s

    def render(self):
        title,sub,_,_=META[self.slug]
        body=self.background()
        if self.slug=='profile':
            body+=self.profile()
        else:
            body+=self.standard_head()
            if self.slug=='projectflow':body+=self.kanban()
            elif self.slug=='hospital':body+=self.flow(['Choose doctor','Select slot','Book','Dashboard'],['Find a specialization','Review availability','Request an appointment','Manage appointment status'])
            elif self.slug=='billiard':
                body+=self.flow(['Browse','Customize','Payment UI','File records'],['Equipment catalog','Build a custom cue','Choose a method','Store account/order data'])
                path='M520 271V557' if self.mobile else 'M60 399H1139'
                body+=self.packet(path,10,0,8,'text',fallback=(520,459) if self.mobile else (600,399))
            elif self.slug=='solar':body+=self.solar()
            elif self.slug=='research':body+=self.research()
            elif self.slug=='portfolio':body+=self.portfolio()
            elif self.slug=='calendar':body+=self.calendar()
            body+=self.footer()
        style='text{font-family:Consolas,Courier New,monospace}.rest{display:none}@media(prefers-reduced-motion:reduce){.moving{display:none}.rest{display:inline}}'
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(sub)}. Original schematic illustration; decorative motion is not live telemetry or measured project activity.</desc><style>{style}</style>{body}</svg>'''


def write_variants(folder, stem, slug):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    files=[]
    for mobile,still,suffix in [(False,False,''),(True,False,'-mobile'),(False,True,'-still'),(True,True,'-mobile-still')]:
        path=folder/(stem+suffix+'.svg')
        path.write_text(Scene(slug,mobile,still).render(),encoding='utf8');files.append(path)
    return files


def picture(prefix, alt):
    alt=escape(alt,quote=True)
    return f'''<picture>
  <source media="(prefers-reduced-motion: reduce) and (max-width: 600px)" srcset="{prefix}-mobile-still.svg">
  <source media="(prefers-reduced-motion: reduce)" srcset="{prefix}-still.svg">
  <source media="(max-width: 600px)" srcset="{prefix}-mobile.svg">
  <img src="{prefix}.svg" width="1200" alt="{alt}">
</picture>'''


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--slug',required=True,choices=META)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--stem',default='workflow')
    args=parser.parse_args()
    write_variants(args.output,args.stem,args.slug)
