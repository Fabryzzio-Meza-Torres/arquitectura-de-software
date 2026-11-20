# R9 — Ejemplos de reranking

Se selecciona una consulta con la mayor mejora y una con la mayor caída de P@3 por dataset.


## FiQA-test — caso de mejora: consulta 2348

Why can't you just have someone invest for you and split the profits (and losses) with him?

ΔP@3 = +0.6667; resultado observado: **mejora**.


| Lista | Posición | ID | Grado | Texto del documento (extracto) |
|---|---:|---|---:|---|
| fused | 1 | 447619 | 1 |  "Why is nobody providing a service that is basically: Give me your money. I will invest it as I see fit. A year later I will return the capital to you, plus half of any profits or losses. This means that if your capital under my management ends up turning a profit, I will keep half of those profits, but if I lose you money, I will cover half those… |
| fused | 2 | 575869 | no juzgado |  "Basically, you either borrow money, or get other people to invest in your business by buying stock or something analogous.  Sometimes you can get people to ""park"" money with you. For example, many people deposit money in a bank checking account. They don't get any interest or other profit from this, they just do it because the bank is a conveni… |
| fused | 3 | 259706 | no juzgado |  "A simple way to ask the question might be to say ""why can't I just use the same trick with my own shares to make money on the way down? Why is borrowing someone else's shares necessary to make the concept a viable one? Why isn't it just the inverse of 'going long'?"" A simple way to think about it is this: to make money by trading something, you… |
| reranked | 1 | 447619 | 1 |  "Why is nobody providing a service that is basically: Give me your money. I will invest it as I see fit. A year later I will return the capital to you, plus half of any profits or losses. This means that if your capital under my management ends up turning a profit, I will keep half of those profits, but if I lose you money, I will cover half those… |
| reranked | 2 | 247486 | 1 |  This means that if your capital under my management ends up turning a profit, I will keep half of those profits, but if I lose you money, I will cover half those losses. The bold part is where you lose me. This absolutely exists with the exception of the loss insurance.  It just requires a lot more than the general retail consumer investor has to … |
| reranked | 3 | 134864 | 1 |  Such an offer has negative value, so it's hard to see how it would make sense to accept it. The offer has two components, one part that you gain and one part that you lose. The gain is that half your losses are covered. The cost is that half your profits are lost. For that to be a net benefit to you, you would have to expect that you will gain mor… |

## FiQA-test — caso de caída: consulta 1393

Which is better when working as a contractor, 1099 or incorporating?

ΔP@3 = -0.6667; resultado observado: **caída**.


| Lista | Posición | ID | Grado | Texto del documento (extracto) |
|---|---:|---|---:|---|
| fused | 1 | 220022 | 1 |  It makes no difference for tax purposes. If you are 1099, you will pay the same amount of taxes as if you formed a corporation and then paid yourself (essentially you are doing this as a 1099 contractor, just not formally). Legally, I don't know the answer.  I would assume you have some legal protections by forming an LLC but practically I think t… |
| fused | 2 | 352640 | 1 |  I am surprised no one has mentioned the two biggest things (in my opinion).  Or I should say, the two biggest things to me.  First, 1099 have to file quarterly self employment taxes.  I do not know for certain but I have heard that often times you will end up paying more this way then even a W-2 employees.  Second, an LLC allows you to deduct busi… |
| fused | 3 | 532932 | 1 |  Unless the amounts involved are very small, it is MUCH better to incorporate. First, incorporation gives you limited liability for your acts as an employee. As an individual, you have unlimited liability. Second, incorporating allows you to deduct (for tax purposes) the costs of doing business, including all of your health insurance, most transpor… |
| reranked | 1 | 234436 | no juzgado |  Another thing to consider, however, is the deductibility of business expenses.  Let's assume that the employer can legitimately hire you as a 1099 contractor.  (Would you be able to telecommute? Would you have a high degree of control over when you worked and when you didn't?  These factors also affect whether you're a true independent 1099 contra… |
| reranked | 2 | 586026 | no juzgado |  Forms 1099 and W2 are mutually exclusive. Employers file both, not the employees. 1099 is filed for contractors, W2 is filed for employees. These terms are defined in the tax code, and you may very well be employee, even though your employer pays you as a contractor and issues 1099. You may complain to the IRS if this is the case, and have them ex… |
| reranked | 3 | 532932 | 1 |  Unless the amounts involved are very small, it is MUCH better to incorporate. First, incorporation gives you limited liability for your acts as an employee. As an individual, you have unlimited liability. Second, incorporating allows you to deduct (for tax purposes) the costs of doing business, including all of your health insurance, most transpor… |

## TREC-COVID-test — caso de mejora: consulta 2

how does the coronavirus respond to changes in the weather

ΔP@3 = +0.3333; resultado observado: **mejora**.


| Lista | Posición | ID | Grado | Texto del documento (extracto) |
|---|---:|---|---:|---|
| fused | 1 | 4bz7xeev | 0 | Substantial Changes in Nitrate Oxide and Ozone after Excluding Meteorological Impacts during the COVID-19 Outbreak in Mainland China [Image: see text] The COVID-19 outbreak in China led to dramatic changes in human activities resulting from the sudden infection prevention and control measures. Here, we use ground-level observations and model simula… |
| fused | 2 | 3svnvozz | 2 | Roles of meteorological conditions in COVID-19 transmission on a worldwide scale The novel coronavirus (SARS-CoV-2/ 2019-nCoV) identified in Wuhan, China, in December 2019 has caused great damage to public health and economy worldwide with over 140,000 infected cases up to date. Previous research has suggested an involvement of meteorological condi… |
| fused | 3 | zespmk29 | 2 | How diseases rise and fall with the seasons—and what it could mean for coronavirus Scientists and doctors have observed for thousands of years that some diseases, such as polio and influenza, rise and fall with the seasons But why? Ongoing research in animals and humans suggests a variety of causes, including changes in the environment (like pH, te… |
| reranked | 1 | w7ycc07b | 2 | Does weather affect the growth rate of COVID-19, a study to comprehend transmission dynamics on human health Abstract The undefendable outbreak of novel coronavirus (SARS-COV-2) lead to a global health emergency due to its higher transmission rate and longer symptomatic duration, created a health surge in a short time. Since Nov 2019 the outbreak i… |
| reranked | 2 | w5kjmw88 | 2 | Weathering the pandemic: How the Caribbean Basin can use viral and environmental patterns to predict, prepare, and respond to COVID-19 The 2020 coronavirus pandemic is developing at different paces throughout the world. Some areas, like the Caribbean Basin, have yet to see the virus strike at full force. When it does, there is reasonable evidence t… |
| reranked | 3 | r1yjphnn | 2 | Does weather affect the growth rate of COVID-19, a study to comprehend transmission dynamics on human health The undefendable outbreak of novel coronavirus (SARS-COV-2) lead to a global health emergency due to its higher transmission rate and longer symptomatic duration, created a health surge in a short time. Since Nov 2019 the outbreak in China, … |

## TREC-COVID-test — caso de caída: consulta 19

what type of hand sanitizer is needed to destroy Covid-19?

ΔP@3 = -0.6667; resultado observado: **caída**.


| Lista | Posición | ID | Grado | Texto del documento (extracto) |
|---|---:|---|---:|---|
| fused | 1 | y777xosr | 2 | Hand Sanitizers: A Review of Ingredients, Mechanisms of Action, Modes of Delivery, and Efficacy Against Coronaviruses BACKGROUND: The emergence of the novel virus, SARS-CoV-2, has posed unprecedented challenges to public health around the world. Currently, strategies to deal with COVID-19 are purely supportive and preventative, aimed at reducing tr… |
| fused | 2 | hma2kvn2 | 1 | COVID-19 and frequent use of hand sanitizers; human health and environmental hazards by exposure pathways Abstract Till date no medication or vaccine is available to cope with the COVID-19 infection and infection rate is increasing drastically across the globe. Only preventive measures and healthy life style with efficient immune system have been s… |
| fused | 3 | eevs62xf | 1 | COVID-19 and frequent use of hand sanitizers; human health and environmental hazards by exposure pathways Till date no medication or vaccine is available to cope with the COVID-19 infection and infection rate is increasing drastically across the globe. Only preventive measures and healthy life style with efficient immune system have been suggested … |
| reranked | 1 | gfyup5aj | 0 | European Task Force on Contact Dermatitis statement on coronavirus 19 disease (COVID-19) outbreak and the risk of adverse cutaneous reactions. Among the basic protective measures against COVID-19, the need to wash hands frequently and in a prolonged way using soap, and to regularly use alcohol-based hand sanitizers is well established for the whole… |
| reranked | 2 | yjg54yyk | 0 | Sanitizer aerosol-driven ocular surface disease (SADOSD)-A COVID-19 repercussion? Since the onset of the COVID-19 pandemic, there has been an advisory for regular and thorough cleaning of hands besides other measures such as social distancing and self-isolation. The rationale for the same is to prevent the transfer of the virus from hands that have… |
| reranked | 3 | eevs62xf | 1 | COVID-19 and frequent use of hand sanitizers; human health and environmental hazards by exposure pathways Till date no medication or vaccine is available to cope with the COVID-19 infection and infection rate is increasing drastically across the globe. Only preventive measures and healthy life style with efficient immune system have been suggested … |