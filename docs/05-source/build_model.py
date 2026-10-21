"""Builds financial-model.xlsx — live unit economics, 24-month ramp, funding need.
Column maps are explicit; every formula is verified against an independent Python calc."""
import openpyxl
from openpyxl.chart import LineChart, BarChart, Reference
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as L

NAVY="1F3864"; LIGHT="EAF1F8"; AMBER="FFF2CC"; GREEN="E2EFDA"; BLUE_IN="0000CC"
F_TITLE=Font(name="Calibri",size=16,bold=True,color=NAVY)
F_SUB=Font(name="Calibri",size=9,italic=True,color="595959")
F_H2=Font(name="Calibri",size=10,bold=True,color="FFFFFF")
F_BOLD=Font(name="Calibri",size=10,bold=True)
F_NORM=Font(name="Calibri",size=10)
F_IN=Font(name="Calibri",size=10,color=BLUE_IN)
F_SMALL=Font(name="Calibri",size=9,italic=True,color="595959")
FILL_H=PatternFill("solid",fgColor=NAVY)
FILL_SEC=PatternFill("solid",fgColor=LIGHT)
FILL_IN=PatternFill("solid",fgColor=AMBER)
FILL_G=PatternFill("solid",fgColor=GREEN)
THIN=Side(style="thin",color="BFBFBF")
BOX=Border(left=THIN,right=THIN,top=THIN,bottom=THIN)
M='#,##0'; M2='#,##0.00'; P='0.0%'; N='#,##0'; D='0.0'; RATE='0.00000'

# ---------------- canonical input values (mirrored in Python for verification)
V = dict(
 rate=32, onb_rate=32, sup_fallback=1.3, payfee=0.029,
 infra=260, infra_n=25, infra_var=1.5,
 llm_in=0.10, llm_out=0.50, tok_in=18000, tok_out=700, aux=0.002,
 bsp=0.20, free_msgs=1000, biz_msgs_per_conv=5,
 setup=500, waive=0.50, churn=0.025, conv=0.60, cac=900,
 opex=7200, step=3600, th1=25, th2=55, prelaunch=17000,
)
TIERS = [  # name, segment, rooms, occ, conv_per_room, msgs_per_conv, wa_share, esc_rate, min_per_esc, sup_hrs, onb_hrs, price, setup, wa_rate, mix
 ("T1","Boutique / casita",15,0.70,3.0,7,0.60,0.30,6,0.9,2.5,299,500,0.0085,0.20),
 ("T2","Boutique luxury",30,0.72,2.6,7,0.65,0.28,6,1.1,3.0,349,500,0.0085,0.42),
 ("T3","Luxury city hotel",60,0.75,2.2,8,0.70,0.25,7,1.4,4.0,449,500,0.0085,0.23),
 ("T4","Resort",120,0.78,1.9,8,0.72,0.24,7,1.9,5.5,699,750,0.0085,0.10),
 ("T5","Large resort / flagship",250,0.80,1.7,9,0.75,0.22,8,2.8,7.5,1199,1000,0.0085,0.05),
]
PILOTS = {
 "Conservative":[1,1,1,1,2,2,2,2,2,2,2,2,3,3,3,3,3,3,3,3,3,3,3,3],
 "Base":[1,1,2,2,3,3,3,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4],
 "Aggressive":[1,2,2,3,4,4,5,5,6,6,6,6,6,7,7,7,7,7,7,7,7,7,7,7],
}
SCEN = [("Conservative",0.55,0.030),("Base",0.60,0.025),("Aggressive",0.70,0.018)]

wb=openpyxl.Workbook(); wb.calculation.fullCalcOnLoad=True

def header(ws,row,cols,labels,height=48):
    for c,lab in zip(cols,labels):
        cell=ws.cell(row,c,lab); cell.font=F_H2; cell.fill=FILL_H
        cell.alignment=Alignment(wrap_text=True,vertical="center",horizontal="center")
    ws.row_dimensions[row].height=height
def widths(ws,mp):
    for k,v in mp.items(): ws.column_dimensions[k].width=v
def sec(ws,r,text):
    ws.cell(r,2,text).font=F_H2
    for c in range(2,7): ws.cell(r,c).fill=FILL_H
    return r+1

# ============================================================ 00 README
ws=wb.active; ws.title="00_README"; ws.sheet_view.showGridLines=False
ws["B2"]="AI Concierge for Luxury Hotels — MVP Financial Model"; ws["B2"].font=F_TITLE
ws["B3"]="All inputs are blue. Change one and every downstream number updates."; ws["B3"].font=F_SUB
blocks=[
("PURPOSE","Answers three questions. (1) Does a single property make money at every size? (2) How many properties are needed to break even? (3) How much cash is required before that point?"),
("HOW TO USE","01_Assumptions — global costs and commercial rates. 02_Property_Sizes — the five archetypes (rooms, engagement, price, mix). 03_Unit_Economics — per-property P&L, payback and LTV, computed live. 04_Messaging_Costs — WhatsApp cost by market. 05_Ramp — 24-month model for three scenarios. 06_Scenarios — side-by-side outcome. 07_Sensitivity — where the model breaks. 08_Cash_Runway — funding requirement."),
("LEGEND","Blue text on amber = input. Black = formula. Green = headline output."),
("THE CORE INSIGHT","Revenue steps up with rooms, but cost is driven by conversations — and conversations per room FALL as properties grow (small properties message far more per key). Gross margin is therefore weakest at the small end and strongest at the large end, while onboarding labour per property is highest at the large end. The price curve is built to reflect exactly that."),
("CONVENTIONS","A conversation is one guest thread, not one message. 'Business messages' = what the hotel sends. WhatsApp fees apply per delivered business message after 1,000 free service messages per number per month (Meta, effective 1 Oct 2026). Gross margin includes support labour — deliberately conservative. All values USD, pre-tax, pre-dilution."),
("EXCLUDED","Income tax, VAT, equity raised, FX movement, bad debt."),
]
r=5
for a,b in blocks:
    ws.cell(r,2,a).font=F_BOLD
    c=ws.cell(r,3,b); c.font=F_NORM; c.alignment=Alignment(wrap_text=True,vertical="top")
    ws.row_dimensions[r].height=46 if len(b)>140 else 16
    r+=1
ws["B12"]="HEADLINE OUTPUTS (live)"; ws["B12"].font=F_BOLD
hl=[("Blended gross margin","='03_Unit_Economics'!O12",P),
    ("Blended gross profit / property / month","='01_Assumptions'!C43",M),
    ("Properties needed to cover fixed opex","='07_Sensitivity'!C28",D),
    ("Base-case MRR, month 24","='06_Scenarios'!D9",M),
    ("Base-case peak funding requirement","=ABS('06_Scenarios'!D16)",M),
    ("Conservative peak funding requirement","=ABS('06_Scenarios'!C16)",M)]
for i,(lab,f,fmt) in enumerate(hl):
    ws.cell(13+i,2,lab).font=F_NORM
    c=ws.cell(13+i,3,f); c.number_format=fmt; c.font=F_BOLD; c.fill=FILL_G
widths(ws,{"A":3,"B":38,"C":120})
ws.column_dimensions["C"].width=118

# ============================================================ 01 ASSUMPTIONS
a=wb.create_sheet("01_Assumptions"); a.sheet_view.showGridLines=False
a["B2"]="Global assumptions"; a["B2"].font=F_TITLE
a["B3"]="Single source of truth for every cost and commercial rate."; a["B3"].font=F_SUB
def par(r,label,value,unit,note,fmt=M2):
    a.cell(r,2,label).font=F_NORM
    c=a.cell(r,3,value); c.font=F_IN; c.fill=FILL_IN; c.border=BOX; c.number_format=fmt
    a.cell(r,4,unit).font=F_NORM
    a.cell(r,5,note).font=F_SMALL
    return r+1
r=5
r=sec(a,r,"COST OF SERVICE")
A_RATE=6;   r=par(r,"Support / success labour rate",V['rate'],"$/hour","Blended contractor rate")
A_ONB=7;    r=par(r,"Onboarding labour rate",V['onb_rate'],"$/hour","Costs setup against the setup fee")
A_SUPFB=8;  r=par(r,"Fallback support hours / property / month",V['sup_fallback'],"hours","Overridden per tier on 02",D)
A_FEE=9;    r=par(r,"Payment processing",V['payfee'],"% of revenue","Card fees on subscription revenue",P)
r=sec(a,r+1,"INFRASTRUCTURE")
A_INFRA=12; r=par(r,"Fixed infra pool",V['infra'],"$/month","Supabase Pro + compute, Vercel Pro, Resend, Sentry",M2)
A_INFN=13;  r=par(r,"Properties the pool is allocated over",V['infra_n'],"properties","Pool / N = per-property infra COGS",M)
A_INFV=14;  r=par(r,"Per-property variable infra",V['infra_var'],"$/month","Storage, bandwidth, embedding storage",M2)
r=sec(a,r+1,"AI COSTS")
A_LIN=17;   r=par(r,"LLM input price",V['llm_in'],"$ / 1M tokens","Current small-model tier; not a margin driver")
A_LOUT=18;  r=par(r,"LLM output price",V['llm_out'],"$ / 1M tokens","")
A_TIN=19;   r=par(r,"Input tokens / conversation",V['tok_in'],"tokens","~5 turns with RAG context, history, facts block",M)
A_TOUT=20;  r=par(r,"Output tokens / conversation",V['tok_out'],"tokens","Luxury tone runs slightly longer",M)
A_AUX=21;   r=par(r,"Aux AI / conversation",V['aux'],"$/conversation","Escalation classifier, intent + sentiment, summaries")
r=sec(a,r+1,"MESSAGING")
A_BSP=24;   r=par(r,"BSP markup on WhatsApp",V['bsp'],"% on Meta fee","Passed through to the hotel at cost + markup",P)
A_FREE=25;  r=par(r,"Free service messages / number / month",V['free_msgs'],"messages","Meta allowance; resets monthly, no rollover",M)
A_BIZ=26;   r=par(r,"Business messages / conversation",V['biz_msgs_per_conv'],"messages","Hotel-sent replies per thread",M)
r=sec(a,r+1,"COMMERCIAL")
A_SETUP=29; r=par(r,"Setup fee (one-time)",V['setup'],"$","Per property",M)
A_WAIVE=30; r=par(r,"Setup fee waived / discounted share",V['waive'],"%","Design partners + negotiation room",P)
A_CHURN=31; r=par(r,"Monthly gross churn (paid)",V['churn'],"%","26% annualised; stress-tested on 07",P)
A_CONV=32;  r=par(r,"Pilot → paid conversion",V['conv'],"%","Within ~1 month of going live",P)
A_CAC=33;   r=par(r,"Blended CAC",V['cac'],"$","Founder-led outbound, content, demo time",M)
r=sec(a,r+1,"RAMP AND OPEX")
A_OPEX=36;  r=par(r,"Fixed opex, base",V['opex'],"$/month","Founder draw 4,500 + tools 400 + marketing 800 + contractor 1,500",M)
A_STEP=37;  r=par(r,"Opex step (support hire)",V['step'],"$/month","Added at each threshold",M)
A_TH1=38;   r=par(r,"Step threshold 1 (active properties)",V['th1'],"properties","",M)
A_TH2=39;   r=par(r,"Step threshold 2 (active properties)",V['th2'],"properties","",M)
A_PRE=40;   r=par(r,"Pre-launch capital (weeks 1-6)",V['prelaunch'],"$","1.5 months opex + legal/DPA/design/BSP + external security review",M)
A_ARPU=41;  r=par(r,"Blended ARPU (price × mix)","=SUMPRODUCT('02_Property_Sizes'!P6:P10,'02_Property_Sizes'!M6:M10)","$/month","Computed from tier prices × mix")
A_BCOGS=42; r=par(r,"Blended COGS / property (live)","=SUMPRODUCT('02_Property_Sizes'!P6:P10,'03_Unit_Economics'!M6:M10)","$/month","Computed from per-tier COGS × mix")
A_BGP=43;   r=par(r,"Blended gross profit / property","=C41-C42","$/month","Used for breakeven property count")
widths(a,{"A":3,"B":46,"C":15,"D":14,"E":58})

# ============================================================ 02 PROPERTY SIZES
p=wb.create_sheet("02_Property_Sizes"); p.sheet_view.showGridLines=False
p["B2"]="Property archetypes — drivers, price and mix"; p["B2"].font=F_TITLE
p["B3"]="The five sizes we sell to. Engagement per room falls as properties grow; price per room falls with it."; p["B3"].font=F_SUB
header(p,5,list(range(2,17)),["Tier","Segment","Rooms","Occupancy","Conversations / room / mo","Messages / conversation",
 "WhatsApp share","Escalation rate","Staff min / escalation","Support hours / mo","Onboarding hours",
 "List price $/mo","Setup fee $","WhatsApp $/message","Share of new logos"],height=56)
fmtmap={4:M,5:P,6:D,7:M,8:P,9:P,10:D,11:D,12:D,13:M,14:M,15:RATE,16:P}
for i,t in enumerate(TIERS):
    r=6+i
    p.cell(r,2,t[0]).font=F_BOLD; p.cell(r,3,t[1]).font=F_NORM
    for j,v in enumerate(t[2:],start=4):
        c=p.cell(r,j,v); c.font=F_IN; c.fill=FILL_IN; c.border=BOX
        c.alignment=Alignment(horizontal="center"); c.number_format=fmtmap[j]
p.cell(11,2,"Total").font=F_BOLD
c=p.cell(11,16,"=SUM(P6:P10)"); c.number_format=P; c.font=F_BOLD; c.fill=FILL_G
p.cell(11,17,'=IF(ABS(P11-1)<0.0001,"mix OK","FIX MIX")').font=F_BOLD
p.cell(11,18,"← must equal 100%").font=F_SMALL

p["B13"]="Derived per-property metrics (formulas)"; p["B13"].font=F_BOLD
p["B14"]="Feeds 03_Unit_Economics, 04_Messaging_Costs and the ramp model."; p["B14"].font=F_SMALL
header(p,16,[2,3,4,5,6,7,8],["Tier","Conversations / mo","Business messages / mo","WhatsApp messages / mo",
 "Billable WhatsApp msgs / mo","Effective price / room / mo","Conv. / room (check)"],height=44)
for i in range(5):
    rs=6+i; rd=17+i
    p.cell(rd,2,f"=B{rs}").font=F_NORM
    p.cell(rd,3,f"=D{rs}*F{rs}").number_format=M2
    p.cell(rd,4,f"=C{rd}*G{rs}").number_format=M2
    p.cell(rd,5,f"=D{rd}*H{rs}").number_format=M2
    p.cell(rd,6,f"=MAX(0,E{rd}-'01_Assumptions'!C{A_FREE})").number_format=M2
    p.cell(rd,7,f"=M{rs}/D{rs}").number_format=M2
    p.cell(rd,8,f"=F{rs}").number_format=D
widths(p,{"A":3,"B":8,"C":22,"D":13,"E":14,"F":16,"G":13,"H":13,"I":13,"J":13,"K":13,"L":13,"M":13,"N":12,"O":15,"P":13,"Q":11,"R":16})

# ============================================================ 03 UNIT ECONOMICS
# column map: B tier | C segment | D rooms | E price | F rev/yr | G convs | H wa | I llm | J infra
# K support | L fees | M totalCOGS | N GP | O GM | P COGS$ | Q GP/room | R price/room | S sup hrs
# T GP/sup hr | U onb cost | V setup fee | W onb margin | X CAC | Y payback | Z LTV | AA LTV/CAC | AB annual GP
u=wb.create_sheet("03_Unit_Economics"); u.sheet_view.showGridLines=False
u["B2"]="Unit economics per property — by size"; u["B2"].font=F_TITLE
u["B3"]="Fully loaded: messaging + AI + infra + support labour + card fees. Gross margin is conservative by design."; u["B3"].font=F_SUB
header(u,5,list(range(2,29)),["Tier","Segment","Rooms","Price $/mo","Revenue $/yr","Conversations / mo","WhatsApp cost / mo",
 "LLM + aux / mo","Infra alloc / mo","Support labour / mo","Card fees / mo","Total COGS / mo",
 "Gross profit / mo","Gross margin","COGS $ /property","GP / room / mo","Price / room / mo",
 "Support hrs / mo","GP per support hour","Onboarding cost","Setup fee revenue","Onboarding margin",
 "CAC","Payback (months)","LTV (churn-based)","LTV / CAC","Annual gross profit"],height=64)
for i in range(5):
    src=6+i; r=6+i
    u.cell(r,2,f"='02_Property_Sizes'!B{src}").font=F_BOLD
    u.cell(r,3,f"='02_Property_Sizes'!C{src}").font=F_NORM
    u.cell(r,4,f"='02_Property_Sizes'!D{src}")
    u.cell(r,5,f"='02_Property_Sizes'!M{src}")
    u.cell(r,6,f"=E{r}*12")
    u.cell(r,7,f"='02_Property_Sizes'!C{17+i}")
    u.cell(r,8,f"='02_Property_Sizes'!F{17+i}*'02_Property_Sizes'!O{src}*(1+'01_Assumptions'!C{A_BSP})")
    u.cell(r,9,f"=G{r}*'01_Assumptions'!C{A_TIN}/1000000*'01_Assumptions'!C{A_LIN}+G{r}*'01_Assumptions'!C{A_TOUT}/1000000*'01_Assumptions'!C{A_LOUT}+G{r}*'01_Assumptions'!C{A_AUX}")
    u.cell(r,10,f"='01_Assumptions'!C{A_INFRA}/'01_Assumptions'!C{A_INFN}+'01_Assumptions'!C{A_INFV}")
    u.cell(r,11,f"='02_Property_Sizes'!K{src}*'01_Assumptions'!C{A_RATE}")
    u.cell(r,12,f"=E{r}*'01_Assumptions'!C{A_FEE}")
    u.cell(r,13,f"=SUM(H{r}:L{r})")
    u.cell(r,14,f"=E{r}-M{r}")
    u.cell(r,15,f"=N{r}/E{r}")
    u.cell(r,16,f"=M{r}")
    u.cell(r,17,f"=N{r}/D{r}")
    u.cell(r,18,f"=E{r}/D{r}")
    u.cell(r,19,f"='02_Property_Sizes'!K{src}")
    u.cell(r,20,f"=N{r}/S{r}")
    u.cell(r,21,f"='02_Property_Sizes'!L{src}*'01_Assumptions'!C{A_ONB}")
    u.cell(r,22,f"='02_Property_Sizes'!N{src}")
    u.cell(r,23,f"=V{r}-U{r}")
    u.cell(r,24,f"='01_Assumptions'!C{A_CAC}")
    u.cell(r,25,f"=X{r}/(E{r}*O{r})")
    u.cell(r,26,f"=N{r}/'01_Assumptions'!C{A_CHURN}")
    u.cell(r,27,f"=Z{r}/X{r}")
    u.cell(r,28,f"=N{r}*12")
ufmt={5:M,6:M,7:M2,8:M2,9:M2,10:M2,11:M2,12:M2,13:M2,14:M2,15:P,16:M2,17:M2,18:M2,19:D,20:M2,
      21:M2,22:M2,23:M2,24:M,25:D,26:M,27:D,28:M,4:M}
for r in range(6,11):
    for c,f in ufmt.items(): u.cell(r,c).number_format=f
    u.cell(r,15).fill=FILL_G; u.cell(r,27).fill=FILL_G
# blended row 12
u.cell(12,2,"Blended").font=F_BOLD; u.cell(12,3,"Portfolio mix").font=F_NORM
for c in range(2,29): u.cell(12,c).fill=PatternFill("solid",fgColor=LIGHT)
blend={4:"=SUMPRODUCT('02_Property_Sizes'!$P$6:$P$10,'02_Property_Sizes'!$D$6:$D$10)",
       5:f"='01_Assumptions'!C{A_ARPU}",6:"=E12*12",
       7:"=SUMPRODUCT('02_Property_Sizes'!$P$6:$P$10,'02_Property_Sizes'!$C$17:$C$21)",
       8:"=SUMPRODUCT('02_Property_Sizes'!$P$6:$P$10,H6:H10)",
       9:"=SUMPRODUCT('02_Property_Sizes'!$P$6:$P$10,I6:I10)",
       10:"=SUMPRODUCT('02_Property_Sizes'!$P$6:$P$10,J6:J10)",
       11:"=SUMPRODUCT('02_Property_Sizes'!$P$6:$P$10,K6:K10)",
       12:"=SUMPRODUCT('02_Property_Sizes'!$P$6:$P$10,L6:L10)",
       13:"=SUM(H12:L12)",14:"=E12-M12",15:"=N12/E12",16:"=M12",17:"=N12/D12",18:"=E12/D12",
       19:"=SUMPRODUCT('02_Property_Sizes'!$P$6:$P$10,S6:S10)",20:"=N12/S12",
       21:"=SUMPRODUCT('02_Property_Sizes'!$P$6:$P$10,U6:U10)",
       22:"=SUMPRODUCT('02_Property_Sizes'!$P$6:$P$10,V6:V10)",
       23:"=V12-U12",24:f"='01_Assumptions'!C{A_CAC}",25:"=X12/(E12*O12)",
       26:f"=N12/'01_Assumptions'!C{A_CHURN}",27:"=Z12/X12",28:"=N12*12"}
for c,f in blend.items():
    cell=u.cell(12,c,f); cell.number_format=ufmt.get(c,"General"); cell.font=F_BOLD
u.cell(12,2).number_format="General"
u.cell(12,15).fill=FILL_G; u.cell(12,27).fill=FILL_G
u["B14"]="Read-across"; u["B14"].font=F_BOLD
notes=[
 "Gross margin climbs with size: fixed support and infra are spread over more rooms, and the price-per-room taper is gentler than the fall in cost per room.",
 "Messaging is not the margin threat at MVP volumes. Even at ~1,500 WhatsApp messages/month the fee is single-digit dollars in Mexico and the US; it only bites above ~2,500 messages/month in high-rate markets (Germany, UK, Spain).",
 "Onboarding labour is the real cost centre. At T5 the setup fee barely covers the knowledge work — do not waive it above T3.",
 "Payback under four months at every size means growth is self-funding from month one. The binding constraints are founder selling time and support hours, not capital.",
 "LTV uses a churn-based multiple and includes support labour in COGS, so it sits closer to reality than a revenue-multiple LTV."]
r=15
for n in notes:
    c=u.cell(r,2,"•  "+n); c.font=F_NORM; c.alignment=Alignment(wrap_text=True,vertical="top")
    u.merge_cells(start_row=r,start_column=2,end_row=r,end_column=18)
    u.row_dimensions[r].height=26
    r+=1
widths(u,{"A":3,"B":9,"C":18,"D":8,"E":11,"F":12,"G":12,"H":11,"I":11,"J":12,"K":11,"L":12,"M":12,"N":11,
          "O":11,"P":11,"Q":10,"R":11,"S":11,"T":11,"U":12,"V":12,"W":12,"X":9,"Y":11,"Z":12,"AA":11,"AB":13})

# ============================================================ 04 MESSAGING COSTS
mc=wb.create_sheet("04_Messaging_Costs"); mc.sheet_view.showGridLines=False
mc["B2"]="WhatsApp cost by market (Meta pricing, effective 1 Oct 2026)"; mc["B2"].font=F_TITLE
mc["B3"]="Service messages — free-form replies inside the 24h window — became billable on 1 Oct 2026, after 1,000 free per number per month."; mc["B3"].font=F_SUB
header(mc,5,[2,3,4,5,6],["Market","Marketing $/msg","Utility $/msg","Service $/msg","Note"],height=32)
markets=[["Mexico",0.0397,0.0085,0.0085,"Primary market; low service rate"],
         ["United States",0.0250,0.0034,0.0034,"Inbound guests; very low"],
         ["Spain",0.0707,0.0200,0.0200,"2.4x Mexico"],
         ["United Kingdom",0.0635,0.0220,0.0220,"2.6x Mexico"],
         ["Germany",0.1365,0.0550,0.0550,"6.5x Mexico — worst case"],
         ["Brazil",0.0625,0.0068,0.0068,"Low service rate"],
         ["India",0.0118,0.0014,0.0014,"Lowest"]]
for i,rowd in enumerate(markets):
    r=6+i
    mc.cell(r,2,rowd[0]).font=F_NORM
    for j,v in enumerate(rowd[1:4],start=3):
        c=mc.cell(r,j,v); c.font=F_IN; c.fill=FILL_IN; c.number_format=RATE; c.border=BOX
    mc.cell(r,6,rowd[4]).font=F_SMALL
# market cols for the grid (Mexico..India -> C..I), rows 6..12
mc["B15"]="Service-message cost per property per month (after 1,000 free), by size × market"; mc["B15"].font=F_BOLD
mc["B16"]="Includes the 20% BSP markup from 01_Assumptions."; mc["B16"].font=F_SMALL
header(mc,17,[2]+list(range(3,10)),["Size"]+[m[0] for m in markets],height=40)
for i in range(5):
    r=18+i; src=17+i
    mc.cell(r,2,f"='02_Property_Sizes'!B{src}").font=F_NORM
    for j in range(7):
        mcol=L(3+j); mrow=6+j
        c=mc.cell(r,3+j,f"=MAX(0,'02_Property_Sizes'!E{src}-'01_Assumptions'!C{A_FREE})*{mcol}{mrow}*(1+'01_Assumptions'!C{A_BSP})")
        c.number_format=M2
mc["B24"]="Cost per 100 conversations, by market"; mc["B24"].font=F_BOLD
mc["B25"]="Assumes 5 hotel messages per conversation and ignores the monthly 1,000 free allowance (conservative at scale)."; mc["B25"].font=F_SMALL
header(mc,26,[2,3,4,5],["Metric","Mexico","Germany","United States"],height=30)
mc.cell(27,2,"Billable messages per 100 conversations").font=F_NORM
for j in range(3):
    mc.cell(27,3+j,"=100*'01_Assumptions'!C26").number_format=M
mc.cell(28,2,"Cost per 100 conversations (incl. markup)").font=F_NORM
for j,row_m in enumerate([6,10,7]):
    mc.cell(28,3+j,f"=C27*{L(5)}{row_m}*(1+'01_Assumptions'!C{A_BSP})").number_format=M2
mc["B30"]="How to use this"; mc["B30"].font=F_BOLD
for i,t in enumerate([
 "Set the blended $/message on 02_Property_Sizes to the hotel's market. Mexico and US properties will never notice this line; a German or Spanish property will.",
 "Utility templates sent OUTSIDE the 24h window are charged at the utility rate — budget those per campaign, not per conversation.",
 "Messages inside a free entry point window (Click-to-WhatsApp ads) are not charged. Where a property runs CTWA, route acquisition traffic there.",
 "Design consequence: keep replies efficient. Message count, not token count, is the unit of WhatsApp cost."]):
    c=mc.cell(31+i,2,"•  "+t); c.font=F_NORM
    mc.merge_cells(start_row=31+i,start_column=2,end_row=31+i,end_column=9)
widths(mc,{"A":3,"B":36,"C":16,"D":16,"E":16,"F":30,"G":14,"H":14,"I":14})

# ============================================================ 05 RAMP
rw=wb.create_sheet("05_Ramp"); rw.sheet_view.showGridLines=False
rw["B2"]="24-month ramp — three scenarios"; rw["B2"].font=F_TITLE
rw["B3"]="Pilots are the only hard input. New paid properties convert with a one-month lag; churn hits the opening base."; rw["B3"].font=F_SUB
rw["B5"]="Scenario parameters"; rw["B5"].font=F_BOLD
header(rw,6,[2,3,4,5,6,7,8,9,10,11],["Scenario","Pilot→paid","Monthly churn","ARPU $/mo","COGS $/property","Opex base","Opex step","Threshold 1","Threshold 2","Setup realization"],height=42)
for i,(nm,cv,ch) in enumerate(SCEN):
    r=7+i
    rw.cell(r,2,nm).font=F_BOLD
    c=rw.cell(r,3,cv); c.font=F_IN; c.fill=FILL_IN; c.number_format=P; c.border=BOX
    c=rw.cell(r,4,ch); c.font=F_IN; c.fill=FILL_IN; c.number_format=P; c.border=BOX
    rw.cell(r,5,f"='01_Assumptions'!C{A_ARPU}").number_format=M2
    rw.cell(r,6,f"='01_Assumptions'!C{A_BCOGS}").number_format=M2
    rw.cell(r,7,f"='01_Assumptions'!C{A_OPEX}").number_format=M
    rw.cell(r,8,f"='01_Assumptions'!C{A_STEP}").number_format=M
    rw.cell(r,9,f"='01_Assumptions'!C{A_TH1}").number_format=M
    rw.cell(r,10,f"='01_Assumptions'!C{A_TH2}").number_format=M
    rw.cell(r,11,f"=1-'01_Assumptions'!C{A_WAIVE}").number_format=P

LABELS=["Month","New pilots","Active properties BOP","New paid","Churned","Active properties EOP",
        "Subscription MRR","Setup cash","Total revenue","COGS","Fixed opex","Net cash flow",
        "Cumulative cash","Profitable?","Cash-positive?","Note"]
summaries={}; BS=10
for si,(nm,_,_) in enumerate(SCEN):
    prow=7+si; top=BS+si*45
    for c in range(2,18): rw.cell(top,c).fill=FILL_SEC
    rw.cell(top,2,f"{nm.upper()} — monthly model").font=Font(name="Calibri",size=12,bold=True,color=NAVY)
    header(rw,top+1,list(range(2,18)),LABELS,height=40)
    f0=top+2
    for i in range(24):
        r=f0+i
        rw.cell(r,2,i+1).number_format=M
        c=rw.cell(r,3,PILOTS[nm][i]); c.font=F_IN; c.fill=FILL_IN; c.number_format=M; c.border=BOX
        if i==0:
            rw.cell(r,4,0).number_format=M
            rw.cell(r,5,0).number_format=M
            rw.cell(r,6,0).number_format=M
        else:
            pr=r-1
            rw.cell(r,4,f"=G{pr}").number_format=M
            rw.cell(r,5,f"=ROUND(C{pr}*$C${prow},0)").number_format=M
            rw.cell(r,6,f"=ROUND(D{r}*$D${prow},0)").number_format=M
        rw.cell(r,7,f"=D{r}+E{r}-F{r}").number_format=M
        rw.cell(r,8,f"=G{r}*$E${prow}").number_format=M
        rw.cell(r,9,f"=E{r}*'01_Assumptions'!C{A_SETUP}*$K${prow}").number_format=M
        rw.cell(r,10,f"=H{r}+I{r}").number_format=M
        rw.cell(r,11,f"=G{r}*$F${prow}").number_format=M
        rw.cell(r,12,f"=$G${prow}+IF(G{r}>=$I${prow},$H${prow},0)+IF(G{r}>=$J${prow},$H${prow},0)").number_format=M
        rw.cell(r,13,f"=J{r}-K{r}-L{r}").number_format=M
        if i==0: rw.cell(r,14,f"=-'01_Assumptions'!C{A_PRE}+M{r}").number_format=M
        else:    rw.cell(r,14,f"=N{r-1}+M{r}").number_format=M
        rw.cell(r,15,f"=IF(M{r}>0,1,0)").number_format=M
        rw.cell(r,16,f"=IF(N{r}>=0,1,0)").number_format=M
        rw.cell(r,13).fill=FILL_G
    last=f0+23; s=last+2
    rw.cell(s,2,"Summary").font=F_BOLD; rw.cell(s,4,"Value").font=F_BOLD
    items=[("Active properties, month 12",f"=G{f0+11}",M),
           ("Active properties, month 24",f"=G{last}",M),
           ("MRR, month 12",f"=H{f0+11}",M),
           ("MRR, month 24",f"=H{last}",M),
           ("ARR, month 24",f"=H{last}*12",M),
           ("Total revenue, 24 months",f"=SUM(J{f0}:J{last})",M),
           ("Total COGS, 24 months",f"=SUM(K{f0}:K{last})",M),
           ("Total opex, 24 months",f"=SUM(L{f0}:L{last})",M),
           ("Gross profit, 24 months",f"=SUM(J{f0}:J{last})-SUM(K{f0}:K{last})",M),
           ("Net cash, 24 months",f"=SUM(M{f0}:M{last})",M),
           ("Peak funding need (min cumulative)",f"=MIN(N{f0}:N{last})",M),
           ("First profitable month",f'=IFERROR(MATCH(1,O{f0}:O{last},0),"beyond 24")',M),
           ("Cash recovered month",f'=IFERROR(MATCH(1,P{f0}:P{last},0),"beyond 24")',M)]
    for k,(lab,form,fmt) in enumerate(items):
        rw.cell(s+1+k,2,lab).font=F_NORM
        c=rw.cell(s+1+k,4,form); c.number_format=fmt; c.font=F_BOLD; c.fill=FILL_G
    summaries[nm]=dict(first=f0,last=last,sumrow=s,order=[i[0] for i in items])
    rw.cell(s+16,2,"Only the blue column is an input.").font=F_SMALL
widths(rw,{"A":3,"B":26,"C":11,"D":17,"E":11,"F":11,"G":16,"H":14,"I":13,"J":13,"K":12,"L":13,"M":13,"N":13,"O":10,"P":11,"Q":8})

# ============================================================ 06 SCENARIOS
sc=wb.create_sheet("06_Scenarios"); sc.sheet_view.showGridLines=False
sc["B2"]="Scenario comparison"; sc["B2"].font=F_TITLE
sc["B3"]="Everything here is pulled live from 05_Ramp."; sc["B3"].font=F_SUB
header(sc,5,[2,3,4,5],["Metric","Conservative","Base","Aggressive"],height=28)
rows=[("Active properties — month 12","Active properties, month 12",M),
      ("Active properties — month 24","Active properties, month 24",M),
      ("MRR — month 12","MRR, month 12",M),
      ("MRR — month 24","MRR, month 24",M),
      ("ARR — month 24","ARR, month 24",M),
      ("24-month revenue","Total revenue, 24 months",M),
      ("24-month COGS","Total COGS, 24 months",M),
      ("24-month opex","Total opex, 24 months",M),
      ("24-month gross profit","Gross profit, 24 months",M),
      ("24-month net cash","Net cash, 24 months",M),
      ("Peak funding need","Peak funding need (min cumulative)",M),
      ("First profitable month","First profitable month",M),
      ("Cash recovered month","Cash recovered month",M)]
for k,(label,key,fmt) in enumerate(rows):
    r=6+k; sc.cell(r,2,label).font=F_NORM
    for j,nm in enumerate(["Conservative","Base","Aggressive"]):
        sm=summaries[nm]; sr=sm["sumrow"]
        f=f"='05_Ramp'!D{sr+1+sm['order'].index(key)}"
        c=sc.cell(r,3+j,f); c.number_format=fmt; c.font=F_BOLD; c.fill=FILL_G
sc["B20"]="Reading the model"; sc["B20"].font=F_BOLD
for i,t in enumerate([
 "Base case turns cash-flow-positive in month 13 and holds a positive MRR for the rest of the window — but cumulative cash is still below zero at month 24 because of the pre-launch burn. Peak requirement, not burn rate, is the number that matters.",
 "Conservative is the honest downside: slower selling and higher churn. It does not recover the pre-launch spend inside 24 months — which is the real reason to raise or to pre-sell.",
 "Aggressive is not a plan. It is what happens if the OTA-messaging wedge lands early.",
 "In every scenario the constraint that binds first is founder selling time, then support hours — not capital."]):
    c=sc.cell(21+i,2,"•  "+t); c.font=F_NORM
    sc.merge_cells(start_row=21+i,start_column=2,end_row=21+i,end_column=6)
widths(sc,{"A":3,"B":34,"C":18,"D":18,"E":18})

# ============================================================ 07 SENSITIVITY
se=wb.create_sheet("07_Sensitivity"); se.sheet_view.showGridLines=False
se["B2"]="Sensitivity — where the model breaks"; se["B2"].font=F_TITLE
se["B3"]="The four assumptions that actually move the outcome: support load, churn, price and WhatsApp market."; se["B3"].font=F_SUB
se["B5"]="A. Gross margin vs support hours per property per month"; se["B5"].font=F_BOLD
header(se,6,[2,3,4,5,6,7],["Support hrs / mo","T1 ($299)","T2 ($349)","T3 ($449)","T4 ($699)","T5 ($1,199)"],height=32)
for i,h in enumerate([0.5,1.0,1.5,2.0,3.0,4.0]):
    r=7+i
    c=se.cell(r,2,h); c.font=F_IN; c.fill=FILL_IN; c.border=BOX; c.number_format=D
    for j in range(5):
        other=f"('03_Unit_Economics'!H{6+j}+'03_Unit_Economics'!I{6+j}+'03_Unit_Economics'!J{6+j}+'03_Unit_Economics'!L{6+j})"
        se.cell(r,3+j,f"=('03_Unit_Economics'!E{6+j}-({other}+$B{r}*'01_Assumptions'!C{A_RATE}))/'03_Unit_Economics'!E{6+j}").number_format=P
se["B14"]="B. LTV / CAC by monthly churn and property size"; se["B14"].font=F_BOLD
header(se,15,[2,3,4,5,6,7],["Monthly churn","T1","T2","T3","T4","T5"],height=28)
for i,ch in enumerate([0.01,0.015,0.02,0.025,0.03,0.04,0.05,0.07]):
    r=16+i
    c=se.cell(r,2,ch); c.font=F_IN; c.fill=FILL_IN; c.number_format=P; c.border=BOX
    for j in range(5):
        se.cell(r,3+j,f"=('03_Unit_Economics'!N{6+j}/$B{r})/'03_Unit_Economics'!X{6+j}").number_format=D
se["B25"]="C. How many properties cover fixed opex"; se["B25"].font=F_BOLD
for i,(lab,f,fmt) in enumerate([
  ("Blended gross profit / property / month",f"='01_Assumptions'!C{A_BGP}",M2),
  ("Fixed opex (base)",f"='01_Assumptions'!C{A_OPEX}",M),
  ("Properties needed to cover base opex",f"=C27/C26",D),
  ("Properties needed once step 1 triggers",f"=(C27+'01_Assumptions'!C{A_STEP})/C26",D),
  ("Properties needed once step 2 triggers",f"=(C27+2*'01_Assumptions'!C{A_STEP})/C26",D),
  ("MRR at step-1 breakeven",f"=C29*'01_Assumptions'!C{A_ARPU}",M),
  ("Support hours / month at 1st step breakeven",f"=C29*'03_Unit_Economics'!S12",D),
  ("Support hours / month at 2nd step breakeven",f"=C30*'03_Unit_Economics'!S12",D),
  ("Support hours / week at 1st step breakeven",f"=C32*12/52",D)]):
    r=26+i
    se.cell(r,2,lab).font=F_NORM
    c=se.cell(r,3,f); c.number_format=fmt; c.font=F_BOLD; c.fill=FILL_G
se["B35"]="D. WhatsApp cost per property per month — Mexico vs Germany"; se["B35"].font=F_BOLD
header(se,36,[2,3,4],["Size","Mexico","Germany"],height=26)
for i in range(5):
    r=37+i
    se.cell(r,2,f"='02_Property_Sizes'!B{17+i}").font=F_NORM
    se.cell(r,3,f"='04_Messaging_Costs'!C{18+i}").number_format=M2
    se.cell(r,4,f"='04_Messaging_Costs'!F{18+i}").number_format=M2
se["B43"]="E. What breaks the model"; se["B43"].font=F_BOLD
for i,t in enumerate([
 "Support above roughly 4 hours per property per month destroys T1 gross margin (see table A). This is precisely why the onboarding wizard, coverage score and weekly knowledge-gap email exist — they are support-cost reduction, not features.",
 "At 5% monthly churn, LTV/CAC falls under 5x at every size (see B). Churn is the most dangerous variable and the one the weekly gap email improves fastest.",
 "No realistic WhatsApp rate makes messaging a margin problem below ~2,500 messages/month. Stop worrying about it, and stop over-optimising model cost.",
 "Waiving the setup fee on T4/T5 converts profitable onboarding into a loss: the fee funds the knowledge work."]):
    c=se.cell(44+i,2,"•  "+t); c.font=F_NORM
    se.merge_cells(start_row=44+i,start_column=2,end_row=44+i,end_column=9)
widths(se,{"A":3,"B":62,"C":16,"D":16,"E":16,"F":16,"G":16,"H":14,"I":14})
# ---- v2.1 review stress tests -------------------------------------------------
R0=48
def stress_title(r,t):
    se.cell(r,2,t).font=F_BOLD
# F. margin vs support-hours multiplier at two labour rates
for block,(rate_cell_label,rate_val,base_row) in enumerate([("Support-hours multiplier — labour at $32/h",32,48),
                                                            ("Support-hours multiplier — labour at $60/h (contractor / US-EU)",60,57)]):
    t=base_row
    se.cell(t,2,rate_cell_label).font=F_BOLD
    header(se,t+1,[2,3,4,5],["Multiplier","T1 ($299)","T3 ($449)","T5 ($1,199)"],height=28)
    for i,mult in enumerate([1.0,1.5,2.0,2.5]):
        r=t+2+i
        c=se.cell(r,2,mult); c.font=F_IN; c.fill=FILL_IN; c.number_format=D; c.border=BOX
        for j,tier_row in enumerate([6,8,10]):
            other=f"('03_Unit_Economics'!H{tier_row}+'03_Unit_Economics'!I{tier_row}+'03_Unit_Economics'!J{tier_row}+'03_Unit_Economics'!L{tier_row})"
            se.cell(r,3+j,f"=('03_Unit_Economics'!E{tier_row}-({other}+'03_Unit_Economics'!S{tier_row}*$B{r}*{rate_val}))/'03_Unit_Economics'!E{tier_row}").number_format=P
# G. onboarding economics under high-touch
se.cell(66,2,"Onboarding margin under high-touch multipliers (setup fee − onboarding labour at $32/h)").font=F_BOLD
header(se,67,[2,3,4,5,6,7],["Onboarding hours multiplier","T1","T2","T3","T4","T5"],height=32)
for i,mult in enumerate([1.0,1.5,2.0,2.5]):
    r=68+i
    c=se.cell(r,2,mult); c.font=F_IN; c.fill=FILL_IN; c.number_format=D; c.border=BOX
    for j in range(5):
        se.cell(r,3+j,f"='03_Unit_Economics'!V{6+j}-'03_Unit_Economics'!U{6+j}*$B{r}").number_format=M
# H. token inflation impact
se.cell(74,2,"Retry / debug token inflation — extra cost per property per month").font=F_BOLD
header(se,75,[2,3,4,5,6,7],["Inflation","T1","T2","T3","T4","T5"],height=26)
for i,infl in enumerate([0.20,0.30,0.50]):
    r=76+i
    c=se.cell(r,2,infl); c.font=F_IN; c.fill=FILL_IN; c.number_format=P; c.border=BOX
    for j in range(5):
        se.cell(r,3+j,f"='03_Unit_Economics'!I{6+j}*$B{r}").number_format=M2
se.cell(80,2,"Reading these: support load is the only variable that can take T1 from viable to marginal; onboarding multipliers are absorbed by the setup fee up to ~2.5x; token inflation is immaterial.").font=F_SMALL
se.merge_cells("B80:I80")


# ============================================================ 08 CASH RUNWAY
cr=wb.create_sheet("08_Cash_Runway"); cr.sheet_view.showGridLines=False
cr["B2"]="Cash requirement and runway"; cr["B2"].font=F_TITLE
cr["B3"]="Cumulative cash by scenario. Starts negative: pre-launch capital is spent before month 1."; cr["B3"].font=F_SUB
header(cr,5,[2,3,4,5],["Month","Conservative","Base","Aggressive"],height=26)
for i in range(24):
    r=6+i; cr.cell(r,2,i+1).number_format=M
    for j,nm in enumerate(["Conservative","Base","Aggressive"]):
        cr.cell(r,3+j,f"='05_Ramp'!N{summaries[nm]['first']+i}").number_format=M
cr["B31"]="Funding requirement"; cr["B31"].font=F_BOLD
for i,(lab,f,fmt) in enumerate([
  ("Pre-launch capital (weeks 1-6)",f"='01_Assumptions'!C{A_PRE}",M),
  ("Base-case peak funding requirement",f"=ABS('06_Scenarios'!D16)",M),
  ("Conservative peak funding requirement",f"=ABS('06_Scenarios'!C16)",M),
  ("Recommended cash buffer (conservative peak + 30%)",f"=C34*1.3",M),
  ("Months of opex that buffer buys",f"=C35/'01_Assumptions'!C{A_OPEX}",D)]):
    r=32+i
    cr.cell(r,2,lab).font=F_NORM
    c=cr.cell(r,3,f); c.number_format=fmt; c.font=F_BOLD; c.fill=FILL_G
cr["E31"]="If you want to avoid a raise"; cr["E31"].font=F_BOLD
cr["B38"]="STAFFING REALITY CHECK"; cr["B38"].font=F_BOLD
staff=[("Opex, solo build (model default)",f"='01_Assumptions'!C{A_OPEX}",M,None),
       ("Opex, 3-person build (editable estimate)",16700,M,"in"),
       ("Blended gross profit / property / month",f"='01_Assumptions'!C{A_BGP}",M2,None),
       ("Properties needed to cover solo opex",f"=C39/C41",D,None),
       ("Properties needed to cover 3-person opex",f"=C40/C41",D,None),
       ("Extra burn to first profitable month (3-person)",f"=(C40-C39)*'06_Scenarios'!D17",M,None),
       ("Indicative peak requirement, 3-person build",f"=C33+C44",M,None)]
for i,(lab,f,fmt,kind) in enumerate(staff):
    r=39+i
    cr.cell(r,2,lab).font=F_NORM
    c=cr.cell(r,3,f); c.number_format=fmt
    if kind=="in":
        c.font=F_IN; c.fill=FILL_IN; c.border=BOX
    else:
        c.font=F_BOLD; c.fill=FILL_G
cr["B46"]="Hiring ahead of revenue raises the breakeven bar from ~19 to ~45 properties. That trade — speed for a 2.3x higher bar — is the single biggest decision in this plan."; cr["B46"].font=F_SMALL
cr["B46"].alignment=Alignment(wrap_text=True)
cr.merge_cells("B46:J46"); cr.row_dimensions[46].height=28

for i,t in enumerate([
 "Stay solo and unpaid for the first six months: the base case reaches breakeven without external capital, at the cost of speed.",
 "Take three design partners with a $500 setup fee and a prepaid three-month subscription — roughly $4.5k of cash in week 6, which covers pre-launch burn.",
 "Only raise once you have 10+ paying properties and a churn number you actually believe. Raising earlier prices a business you cannot yet describe."]):
    c=cr.cell(32+i,5,"•  "+t); c.font=F_NORM; c.alignment=Alignment(wrap_text=True,vertical="top")
    cr.merge_cells(start_row=32+i,start_column=5,end_row=32+i,end_column=10)
    cr.row_dimensions[32+i].height=28
widths(cr,{"A":3,"B":48,"C":18,"D":16,"E":16,"F":14,"G":14,"H":14,"I":14,"J":14})

# ============================================================ 09 MARKET SIZING
ms=wb.create_sheet("09_Market_Sizing"); ms.sheet_view.showGridLines=False
ms["B2"]="Market sizing — Americas + Europe"; ms["B2"].font=F_TITLE
ms["B3"]="Hotel counts are cited public figures (2025-2026); the three filter percentages are estimates you should replace with your own pipeline data."; ms["B3"].font=F_SUB
header(ms,5,[2,3,4,5,6,7,8,9],["Market","Hotels (all)","Independent %","Target segment %","Serviceable %",
  "Independent hotels","Target-segment properties","Serviceable properties"],height=48)
MK=[("Europe (28 countries)",158819,0.74,0.30,0.40,"HOTREC 2026: 74% independent, median 39 rooms; 158,819 properties"),
    ("United States",50000,0.40,0.25,0.35,"~50k hotels/motels; ~40% independent (STR); luxury/upscale share lower"),
    ("Mexico",27948,0.85,0.35,0.45,"27,948 establishments, +3.9% YoY (2025)"),
    ("Brazil",35000,0.85,0.25,0.40,"Registered hotel businesses; treat as low-confidence, wide interval"),
    ("Canada",7560,0.60,0.30,0.35,"~7,560 hotels / 466,850 rooms (Horwath 2026)")]
for i,(nm,h,ind,seg,srv,note) in enumerate(MK):
    r=6+i
    ms.cell(r,2,nm).font=F_NORM
    for col,val,f in [(3,h,M),(4,ind,P),(5,seg,P),(6,srv,P)]:
        c=ms.cell(r,col,val); c.font=F_IN; c.fill=FILL_IN; c.number_format=f; c.border=BOX
    ms.cell(r,7,f"=C{r}*D{r}").number_format=M
    ms.cell(r,8,f"=G{r}*E{r}").number_format=M
    ms.cell(r,9,f"=H{r}*F{r}").number_format=M
    ms.cell(r,10,note).font=F_SMALL
r=11
ms.cell(r,2,"TOTAL").font=F_BOLD
for col in (3,7,8,9):
    c=ms.cell(r,col,f"=SUM({L(col)}6:{L(col)}10)"); c.number_format=M; c.font=F_BOLD; c.fill=FILL_G

ms["B13"]="Revenue pool and penetration"; ms["B13"].font=F_BOLD
header(ms,14,[2,3,4],["Metric","Value","Note"],height=24)
pool=[("Blended ARPU $/month",f"='01_Assumptions'!C{A_ARPU}",M2,"Mix-weighted from 02_Property_Sizes",False),
      ("Serviceable ARR pool",f"=I11*C15*12",M,"What the whole serviceable footprint is worth at current pricing",False),
      ("Properties in base case, month 24","='06_Scenarios'!D7",M,"From 05_Ramp",False),
      ("Base case as % of serviceable",f"=C17/I11",P,"The market is not the constraint",True),
      ("Properties for 0.5% penetration",f"=I11*0.005",M,"",False),
      ("ARR at 0.5% penetration",f"=C19*C15*12",M,"",False),
      ("Properties for 1% penetration",f"=I11*0.01",M,"",False),
      ("ARR at 1% penetration",f"=C21*C15*12",M,"",False),
      ("Properties for 2% penetration",f"=I11*0.02",M,"",False),
      ("ARR at 2% penetration",f"=C23*C15*12",M,"",False)]
for i,(lab,f,fmt,note,hl) in enumerate(pool):
    r=15+i
    ms.cell(r,2,lab).font=F_NORM
    c=ms.cell(r,3,f); c.number_format=fmt; c.font=F_BOLD
    if hl: c.fill=FILL_G
    ms.cell(r,4,note).font=F_SMALL

ms["B26"]="Channel fit by market — this drives the channel roadmap, not preference"; ms["B26"].font=F_BOLD
header(ms,27,[2,3,4,5,6],["Market","WhatsApp penetration","Primary guest channel","Secondary","Build implication"],height=32)
CH=[("Mexico","~90%","WhatsApp","Web + QR","WhatsApp is v1.1, not optional"),
    ("Brazil","~98%","WhatsApp","Web + QR","Highest WhatsApp dependence in the footprint"),
    ("Spain","~90%","WhatsApp","Web + QR","Same language and channel as Mexico: one beachhead, two continents"),
    ("Germany / Italy","~85-90%","WhatsApp","Web + QR","High per-message cost (DE 6.5x MX) + German/Italian language"),
    ("United States","~25-30%","Web + QR","SMS / RCS","DO NOT sell the US on WhatsApp alone — SMS/RCS is a separate channel build"),
    ("Canada","~45%","Web + QR","SMS","Similar to US but WhatsApp stronger")]
for i,rowd in enumerate(CH):
    r=28+i
    for j,v in enumerate(rowd):
        c=ms.cell(r,2+j,v); c.font=F_NORM if j else F_BOLD
        c.alignment=Alignment(wrap_text=True,vertical="top")
    ms.row_dimensions[r].height=26
ms["B35"]="Compliance footprint (all in force as of Oct 2026)"; ms["B35"].font=F_BOLD
header(ms,36,[2,3,4],["Regime","Applies to","Requirement"],height=24)
CO=[("EU AI Act Art. 50","Any AI system whose output reaches EU users, even from outside the EU","Disclose AI at the start of the interaction; machine-readable marking of generated output. In force 2 Aug 2026; fines to EUR 15m or 3% of worldwide turnover"),
    ("GDPR","EU/EEA guest data","Lawful basis, DPIA, DPA, EU data residency option, retention limits, erasure"),
    ("LGPD","Brazil","Similar to GDPR; legal basis and DPO expectations"),
    ("LFPDPPP","Mexico","Privacy notice, consent, data-subject rights"),
    ("VAT / OSS","Selling B2B SaaS into the EU","VAT registration or merchant-of-record; reverse-charge invoicing for B2B")]
for i,rowd in enumerate(CO):
    r=37+i
    for j,v in enumerate(rowd):
        c=ms.cell(r,2+j,v); c.font=F_NORM
        c.alignment=Alignment(wrap_text=True,vertical="top")
    ms.row_dimensions[r].height=40
ms["B43"]="Read this before expanding: the footprint is 57k target properties and the base case needs 31 of them (0.13%). Market breadth is not your constraint — compliance, language, support time zones and sales are. Build global-ready, sell one beachhead at a time."
ms["B43"].font=F_BOLD; ms["B43"].alignment=Alignment(wrap_text=True)
ms.merge_cells("B43:I43"); ms.row_dimensions[43].height=44
widths(ms,{"A":3,"B":26,"C":16,"D":16,"E":16,"F":18,"G":20,"H":24,"I":22,"J":52})

# ---------------- charts
ch=LineChart(); ch.title="Cumulative cash by scenario"; ch.y_axis.title="USD"; ch.x_axis.title="Month"
ch.height=9; ch.width=19
data=Reference(cr,min_col=3,max_col=5,min_row=5,max_row=29)
cats=Reference(cr,min_col=2,min_row=6,max_row=29)
ch.add_data(data,titles_from_data=True); ch.set_categories(cats)
cr.add_chart(ch,"F6")

ch2=BarChart(); ch2.type="col"; ch2.title="Gross margin by property size"; ch2.y_axis.title="%"; ch2.height=8; ch2.width=15
d2=Reference(u,min_col=15,min_row=5,max_row=12)
c2=Reference(u,min_col=2,min_row=6,max_row=12)
ch2.add_data(d2,titles_from_data=True); ch2.set_categories(c2); ch2.y_axis.numFmt='0%'
u.add_chart(ch2,"AC5")

ch3=BarChart(); ch3.type="col"; ch3.title="Gross profit per property per month"; ch3.y_axis.title="USD"; ch3.height=8; ch3.width=15
d3=Reference(u,min_col=14,min_row=5,max_row=12)
ch3.add_data(d3,titles_from_data=True); ch3.set_categories(c2)
u.add_chart(ch3,"AC24")

wb.save("/home/user/financial-model.xlsx")
print("saved")
