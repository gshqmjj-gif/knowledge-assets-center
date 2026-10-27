---
title: 我把 3 个 Star 过万的 Skill 串起来，搭了一条能“复刻任意软件”的流水线
source_type: wechat_article
source_url: https://mp.weixin.qq.com/s/bs7SwRd7GrVEiaI_ARDP0g
author: AI开源无界
published_date: '2026-10-26'
ingested_at: '2026-10-26 20:53:34'
tags:
- AI
- AI开源无界
- 微信公众号
keyframes: []
snippets: []
assets: []
---

最近“AI 复刻软件”这类内容很多。不少文章喜欢把它说成一句话的事：装几个工具，把目标丢给 AI，等它跑完，一个差不多的软件就有了。
真到自己电脑上跑，一般不会这么顺。Node 版本不对，MCP 没挂上，Docker 起不来，目标选得太大，AI 一口气吐出一大堆分析，看着挺热闹，其实能用的没几条。
不过这套东西有它自己的用处。
把 REA、Reverse-skill、PentAGI 这三个 Skill 搭起来以后，能做一件挺完整的事：看到一个软件功能，先让 AI 去查它是怎么实现的，再按我们自己的技术栈写一个新版本，最后在上线前帮忙找一轮安全问题。
这一套组合下来，基本能复刻任何软件，但禁止逆向和加混淆的别碰，这玩意儿只能拿来学习使用，只复刻允许复刻的软件，没有风险。
整体流程大概是这样：

![配图](https://mmbiz.qpic.cn/mmbiz_png/2s3aIh6gGYHIS9LZevKicIq1mbcB1VgjWEJPHOGHqqt77KsT5VicZD80sER14hKYxtWEJo0CicTONoopB98Lf5pn6T18Q7cLMAs2Y4oCqib2HZw/640?wx_fmt=png&from=appmsg)

# 这三个 Skill 各管一段
整个流程看着挺绕，我们捋一下，其实各自干得活儿并不多。

![配图](https://mmbiz.qpic.cn/mmbiz_png/2s3aIh6gGYERBIPRJt5pR9KZ29KBdfRddcqjOtvLW12yK2pwpr3RibJUjsL2M6LcwibtRzqdpmn3weickicZtPrDrCpslNosH6WjssUibMdcm0j0/640?wx_fmt=png&from=appmsg)
REA 负责分析目标。它能看网页、JavaScript 应用、Electron 应用、.NET 程序、Android 安装包，也能配合 Ghidra、IDA、Hopper 这些工具看原生二进制文件。它比较实用的一点，是会给结论带证据，比如它看到了哪个文件、哪段代码、哪次运行结果。
REA目前36万 Star，是有真东西的。

![配图](https://mmbiz.qpic.cn/sz_mmbiz_png/2s3aIh6gGYGPSa32TmUwiaMqyu2G2FicjuLiciccaTVic7O7emUVocQuM7cOskMXRGLxXY2YiaaAYZEKG1HFVhS0qSqUBCg6loQtN4fdCiafhe6ibb0/640?wx_fmt=png&from=appmsg)
Reverse-skill 负责帮 AI 选路。逆向要用的工具太多了，APK 有一套，网页有一套，二进制文件又得换一套。新手很容易一开始就选错。Reverse-skill 里面写的是各类任务大概怎么走、会用到哪些工具、本机还缺什么。
这个 Skill 在 GitHub 拿到了4.3万 Star，能力是经过社区验证了的，拿它跑一点儿问题都没有。

![配图](https://mmbiz.qpic.cn/mmbiz_png/2s3aIh6gGYFibqvricpTH81AAiaLaRPiaLGHV6dGZiaiaEBzspQ9A6vQmUewSiav9SNndDY2d2o8icqb867e9jnRfR6aHrMvrfXYumicoiccxBghQj0Sc/640?wx_fmt=png&from=appmsg)
PentAGI 放在最后。等我们把自己的版本做出来，又准备上线，它可以帮忙跑一轮安全测试，找找接口暴露、输入校验、配置不当这类问题。
PentAGI 也是3.2万 Star 的生产力级别工具，版本出来拿它做几轮测试，基本就稳妥了。

![配图](https://mmbiz.qpic.cn/sz_mmbiz_png/2s3aIh6gGYHd2qbBoEdWXG4dCO8NPPQHMuIr3HhlaxfLpWicyRhR5myJspPIkmnkyNZxWaLXrBb2xcBUctxakoW7I69Js7U7aLMvGtnjzLrQ/640?wx_fmt=png&from=appmsg)
中间还需要一个支持 MCP 的 AI 编程客户端。MCP 可以先理解成一个插座，AI 客户端通过它调用 REA 这类本地工具。你本机已经有哪个客户端，就用哪个。账号、订阅、网络环境这些前置条件，每个人情况不一样，这里不展开。

# 复刻之前，先把边界说清楚
很多人看到“复刻软件”，第一反应是把别人的东西原样搬过来。
我不建议这么干，原样搬代码、搬素材，容易出问题，也没多大意义，你做一个一模一样的东西有什么用呢？更麻烦的是，很多东西不能碰，尤其是明确禁止逆向，有混淆加密的，不要去做技术对抗。
我自己用这套流程时，会先把边界写清楚：只分析自己的项目、开源项目，或者明确拿到授权的目标，让AI去干活儿前，先让它把风险都捋一遍，是否合规要明确。
加密保护、登录后的数据、别人的私有接口、商业软件的完整功能和资源文件，都别碰。工具拿来做学习或兼容实现都行，别用来碰不该碰的东西。

![配图](https://mmbiz.qpic.cn/mmbiz_png/2s3aIh6gGYFmJPG8lICedtKruFCib8Gp5LaPzclXMMY4jpicpwmThJHsF7v1qFzxWfFCIPh8RN1Xh6LHRRvTk3yEOLq0B6p9CkwjvugHBbSXg/640?wx_fmt=png&from=appmsg)
这里说的“复刻”，我理解成先把功能行为弄明白，再写自己的实现。比如我们想研究一个本地待办工具里的搜索功能，先别急着扒代码，先把这些问题弄清楚：
这些问题有了答案，后面才好写。

# 前期准备
这套流程对环境有点要求，列个简单的准备清单：
PentAGI 对机器资源有要求：
官方 README 里写的最低配置是 2 核 CPU、4GB 内存和 20GB 可用磁盘。电脑比较紧张的话，可以先不装它，前面的分析和重写流程不受影响，PentAGI 只是对我们的成果软件进行漏洞检测。
我一般会单独建一个目录，比如在桌面建一个ai-reverse-lab。练习项目、分析结果、重写版本都放进去，别让 AI 在整个硬盘里乱翻，后面排查问题也方便。
接工具的时候，我会让 AI 先读 README，先检查环境，别直接装东西。可以这么发：

```
我想在本机接入 REA 和 reverse-skill，用来分析我自己有权分析的软件功能。请先阅读这两个仓库的 README：1. https://github.com/morluto/rea2. https://github.com/zhaoxuya520/reverse-skill我的系统是：【Windows / macOS / Linux】。请你先检查当前环境，不要直接安装东西。把已经满足的条件、缺失的工具、接下来建议执行的命令列出来。每个命令都说明作用、风险和预期结果，等我确认后再继续。
```

![配图](https://mmbiz.qpic.cn/sz_mmbiz_png/2s3aIh6gGYFmHPeibicJR8LqNsBYtGYwH3icKyPYLMOmAsR8Y1Wd8oE0DHGcwDdCN3n2sM3OXUrzwmf0riblsUvUNRLbFdxKq6dvPsHicsUAlicZw/640?wx_fmt=png&from=appmsg)
装完以后，别听它一句“装好了”就算完。我会让它做一次最小测试：

```
请确认 REA 和 reverse-skill 是否已经能被当前客户端调用。请分别做一次最小测试，并告诉我：1. 哪个工具已经可用2. 哪个工具还没有接入成功3. 如果有问题，下一步应该怎么排查
```
拿不出测试结果，就先当没装好。

# 第一次目标选小一点
我不建议第一次就拿大型软件练手。
我会先自己写一个小项目，或者找一个结构简单的开源项目。比如一个纯前端 Todo List，一个本地 Markdown 预览器，一个简单小游戏。
为了把流程说清楚，后面我都拿“Todo List 里的搜索功能”来举例。

![配图](https://mmbiz.qpic.cn/mmbiz_png/2s3aIh6gGYFgnFqzttCHqJI54sq1bz6BUdmp6oM0mJKeS4qtDXl7iboAYSiceR9gsdxndPpDUgUJASib7QTW9pScdvb8TBsFsL4nGvj0cxeOwg/640?wx_fmt=png&from=appmsg)
这个目标不大，但有输入，有输出，有状态变化，也有空结果、大小写、删除后刷新这些边界情况，拿来练手够了。
我会先把目标写得尽量窄：

```
我想分析一个本地 Todo List 项目里的搜索功能。我只关注这一个功能：输入关键词后，页面如何筛选待办事项。请先帮我确认分析边界：1. 不涉及登录、账号、网络请求2. 不分析项目里的其他功能3. 不复制项目里的代码和资源4. 如果目标描述不清楚，请先向我提问
```
目标写窄一点，AI 就不容易顺着项目一路乱看，分析出来的内容也会少很多，至少看得完。

![搜索功能分析结论](https://mmbiz.qpic.cn/sz_mmbiz_png/2s3aIh6gGYHRpGQSP9oA9A1wwpzJw3CvwQicxSiasjIKJrf6fduadaJebmFFj7IX3ITfP3NgzVjL9RKUoo1icXjvshkZG1pI4dibLzQe6yeAtZ4/640?wx_fmt=png&from=appmsg)

# Reverse-skill 先帮 AI 选路
确定目标以后，我会先让 Reverse-skill 判断这次该走哪条路线。

```
请根据 reverse-skill 的路由规则，判断这次任务属于哪种分析类型。目标是：本地 Todo List 项目里的搜索功能。请告诉我：1. 应该走哪条分析路线2. 需要哪些工具3. 本机已经有哪些工具4. 缺哪些工具5. 哪些安装动作需要我确认请先给方案，不要直接安装。
```
这一步会多花几分钟，路线选对了，后面能少很多瞎试。

![选路线和确认本机工具是否齐全](https://mmbiz.qpic.cn/sz_mmbiz_png/2s3aIh6gGYHc45t11Xs0g7PDAozLeicqLBAVg3zmP4V9pnvfQFNalAa59CJRdnxRfwhMS3fB8ZpJS5jicIV3piavJ0wLBxaRMEOUVaIeFEgic7M/640?wx_fmt=png&from=appmsg)
比如一个纯前端项目，通常没必要上二进制分析工具；一个 Android 安装包，也不用先折腾网页抓包。工具选错以后，AI 也能跑出一堆东西，但那些东西很可能跟我们要找的功能没什么关系。

# 用 REA 正式分析
路线确认以后，再让 REA 正式分析。
我会这样说：

```
请用 REA 分析这个 Todo List 项目里的搜索功能。我需要一份带证据的分析结果，包含：1. 这个功能整体做了什么2. 用户输入关键词后，程序从哪里开始处理3. 关键的函数、文件和调用关系4. 每条结论对应的证据，包括文件位置、代码位置或运行观察5. 哪些地方还不能确定如果证据不够，请直接写“不确定”，不要猜。
```
拿到结果以后，我会先挑几条结论对着页面试一下。

![搜索功能 REA 分析结论](https://mmbiz.qpic.cn/sz_mmbiz_png/2s3aIh6gGYHWh8ibGlkYVvQONiaGWNL7BibWrU1mcSgiaz1IF5WowOvRUUZe9kCMv8TMb0F5P1UmGhKYduCxANibfic5JoFRxJdu1tkNcN6j9K9ibQ/640?wx_fmt=png&from=appmsg)
比如它说搜索时会忽略大小写，那我就输入一个大写关键词，再输入一个小写关键词，看结果是不是一样。
比如它说某段逻辑在某个文件里，我会让它把 Evidence 展开，看看它到底读了哪几段。只说“相关逻辑在某文件里”不够，后面写代码时很容易飘。
如果结论写得很空，我会继续追问：

```
请展示这次分析的 Evidence 记录。我需要知道你具体读取了哪些文件、哪些代码片段、哪些运行结果。请把每条结论和对应证据放在一起。如果某条结论没有证据，请标记为“推测”。
```
分析结果里最好把确定和不确定分开，每条都写得特别满，我反而会多留个心眼。

![配图](https://mmbiz.qpic.cn/mmbiz_png/2s3aIh6gGYHZW7qqvBVlQiaa0Piaq0gdVeJCRuV17DV47VO5GMicTTibm6SIuicasQSFc8w5FcuVD2Yez0brTGXV82DkDxag8Mvf3rVsNWeYRtcY/640?wx_fmt=png&from=appmsg)

# 动手写之前，先让它把话说明白
REA 给出的结果，有时候还是偏技术。它给出的结果对小白很不友好，像这种：

![配图](https://mmbiz.qpic.cn/mmbiz_png/2s3aIh6gGYF1Mx6ibx9wRBGkGfj6WczJyv4a62DibeNibPQ4k9e9X3v7cAiax1LfokyqoiaWOeJDswHiaZOqQ83TYOLmdrbmz5y2UXgsmawjp2rDc/640?wx_fmt=png&from=appmsg)

![配图](https://mmbiz.qpic.cn/mmbiz_png/2s3aIh6gGYEVMgrW1VWvL1ImkVQu3CD1vib1PpqUxNoSqraoUpak1SnOfhW5XT0V2DtxtjCblpWMQicQJItdltxTjw7eJnI0geD3zdyV74EoA/640?wx_fmt=png&from=appmsg)
这时候别急着写代码，先让 AI 把那堆分析翻成一份人话说明，再整理成实现规格。

```
请把上面的分析结果改写成一份小白能看懂的说明。我需要知道：1. 用户输入是什么2. 程序输出是什么3. 中间经过哪些处理4. 有哪些边界情况5. 哪些地方需要和原版行为保持一致最后请整理成一份实现规格。不要复制目标项目的代码、文案、样式和资源。
```
拿 Todo List 搜索来说，整理出来可能长这样：

```
功能：搜索待办事项输入：用户在搜索框输入关键词。处理：1. 获取当前关键词2. 去掉前后空格3. 将关键词和待办标题统一转成小写4. 找出标题中包含关键词的待办事项5. 更新页面列表输出：显示匹配到的待办事项。边界情况：1. 搜索框为空时显示全部待办2. 没有匹配结果时显示“没有找到相关内容”3. 删除当前匹配项后，搜索结果立即刷新4. 连续输入时不需要刷新页面
```
有了这份说明，后面写代码时至少有东西对照。没有它，AI 很容易只做出个“看着像”的东西，一用就发现边界情况对不上。

# 然后让 AI 写自己的版本
到这一步，才轮到 AI 客户端动手写。
我会把要求说得清楚一点：

```
请根据刚才整理的实现规格，用 HTML、CSS 和 JavaScript 写一个独立版本。要求：1. 不复制目标项目的代码2. 不使用目标项目的图片、图标和文案3. 先给文件结构4. 先列出测试用例5. 每个文件说明作用6. 给出本地运行方法7. 写完以后先自己运行测试8. 告诉我哪些测试通过，哪些没有通过
```

![配图](https://mmbiz.qpic.cn/sz_mmbiz_png/2s3aIh6gGYHh0icxpDTZOricmPyd2Yn4msadXeAr7Zzxo3icVZsvzZVvwxkovl6lUy6GUPCFqmYMGluic0pZnQiaRYpYa3owGcskYiaMLz4mdGmYA/640?wx_fmt=png&from=appmsg)

![配图](https://mmbiz.qpic.cn/mmbiz_png/2s3aIh6gGYE0POmKrtHLst5O3FicR2OtoQ4PXl3yH8ktFLOdB1dvnqPW3UWHmoRQfvoia7t35ibWBJRRj8iaVAIFABlHCrymrlM6Wp0oVfwVZl4/640?wx_fmt=png&from=appmsg)

# 写完了，先别急着信
自己的版本跑起来以后，我会让 AI 做一次行为对比。

```
请把原版功能和新版功能逐项对比。重点检查：1. 相同输入下，输出是否一致2. 空输入、特殊字符、超长文本的处理是否一致3. 有没有原版能处理、新版漏掉的情况请把差异列成表格，不要只说“基本一致”。
```
差异很少，这个小功能就差不多能用了。

![配图](https://mmbiz.qpic.cn/mmbiz_png/2s3aIh6gGYHWocEibdmlwOn4V2Jyy9nzcgSEx55UEEuTicFTLPFOohj0OVZfCWnicGEgVgDoBr12hfIOdEKGdYDrscicianniccMcEr9oq0iclJ8bg/640?wx_fmt=png&from=appmsg)

![配图](https://mmbiz.qpic.cn/mmbiz_png/2s3aIh6gGYHRkoKTZsicYPvDQ67UrfwgpfRiaibS6MZVGxv4FfgmCQS0o5TaT08x6Dg3j9mPoxk9yMNjOxdM9DKS74G7ly16Oykftsonccs0qk/640?wx_fmt=png&from=appmsg)
差异很多，也别急着让 AI 一口气全改。一次只修一个问题，修完就重新跑测试，后面会少很多麻烦。

# PentAGI 放在上线前
如果只是写了个本地页面，自己跑一跑，PentAGI 可以先不用。
等项目准备上线，又涉及登录、表单、文件上传、数据库、后台、对外 API 这些东西，再考虑它。
我会先把项目跑在本地或测试服务器里，再让 PentAGI 只测这个目标：

```
这是我自己搭建并有权测试的系统，测试地址是：【本地地址或测试地址】。请使用 PentAGI 只测试这个目标。不要访问其他域名、其他内网地址和无关服务。测试结束后，请按严重程度整理结果：1. 严重和高危问题2. 中危问题3. 低危和提示项每个问题都告诉我：如何复现、影响是什么、应该怎么修。
```
报告出来以后，也别想着一次全修完。
我一般先看严重和高危，中危集中处理，低危先记下来，修完以后再测一遍。
PentAGI 能帮忙找问题，但不能拿它当系统安全的证明。依赖漏洞、弱密码、权限配置、业务逻辑漏洞，最好分开检查。

# 真跑不通，常见就这几种情况
跑不通的话多半是某个环节没交代清楚。
如果 AI 说找不到 REA，先让它检查 MCP 配置，再重启客户端，重启以后再让它做一次最小测试。
如果终端提示command not found，一般是对应工具没装，或者装了但终端没识别。把完整报错贴给 AI，不要只说一句“报错了”。

```
我在【终端 / PowerShell】执行了【命令】。完整报错如下：【粘贴完整报错】请先解释这条报错是什么意思，再给下一步操作。每次只处理一个问题。
```
如果分析结果没有证据，先别让它写代码。让它补 Evidence，补不出来的地方就标成“不确定”。
如果新版能跑，但行为不一样，先别让它继续“优化一下”。让它把差异列出来，按影响程度排个序，我们一次只处理一个问题。

# 大型复杂软件，别指望一次还原到位

![配图](https://mmbiz.qpic.cn/mmbiz_png/2s3aIh6gGYHUvCODCYADHQWJ8MLNFHCDRIwuTv2Be7N5zahZHiaPqUQGar3zQz2TPZ77QFPNH7s6NUeOdScBuchdnp6lV4G1mT4wv5OfC9Sw/640?wx_fmt=png&from=appmsg)
这套流程确实能做复刻，不过做出来的东西，未必能做得100%像。
小功能通常好办。一个搜索框、一个按钮、一个本地小游戏，AI 能看到代码，也能观察行为，还原度可以做得很高。
大型复杂软件就麻烦多了。尤其是带后端、账号体系、数据库、推荐算法、风控规则和并发逻辑的项目，AI 能先还原的往往只是本地可见的那部分。服务器里的逻辑、历史数据和工程体系，看不到就没法完整还原。
所以前面说的“复刻”，落到实际操作里，通常就是先做一个能跑、行为接近的版本。能有多像，要靠测试用例一点点对。

# 开源地址
REA：https://github.com/morluto/rea
Reverse-skill：https://github.com/zhaoxuya520/reverse-skill
PentAGI：https://github.com/vxcontrol/pentagi
这个公众号长期分享实用开源项目。如果你不想逐篇翻阅历史文章，可以直接关注微信公众号“AI开源无界”，通过后台留言与我们互动交流。

![图片](https://mmbiz.qpic.cn/mmbiz_jpg/2s3aIh6gGYFfZXia4DAeVCicQS8ZNkibP5f5jIw7qric3BuaEB3ia3Bjw4Z64VXrTNcACk4roVJnVibVsRIVsUAz8he095ZrROezpQQK0xr85LI44/640?wx_fmt=jpeg&from=appmsg&watermark=1&wxfrom=5&wx_lazy=1&tp=webp#imgIndex=8)
