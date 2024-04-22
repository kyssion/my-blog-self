# quartz 简介
Quartz.NET是一个强大、开源、轻量级的任务调度框架。任务调度在我们的开发中经常遇到，如说：每天晚上三点让程序或网站执行某些代码，或者每隔5秒种执行一个方法等。Windows计划任务也能实现类似的任务调度，但是Quartz.net有一些有优秀的特性，如：数据库支持，集群，插件，支持cron-like表达式等等。  

- 官网：http://www.quartz-scheduler.net/
- 源码：https://github.com/quartznet/quartznet
= 示例：https://www.quartz-scheduler.net/documentation/quartz-3.x/quick-start.html 

在使用Quart.net前，我们先理解下quartz的构成和基本工作流程，Quartz包含以下五个基本部分

```
Scheduler           调度器，quartz工作时的独立容器
Trigger             触发器，定义了调度任务的时间规则
Job                 调度的任务
ThreadPool          线程池（不是clr中的线程池），任务最终交给线程池中的线程执行
JobStore            RAWStore和DbStore两种，job和trigger都存放在JobStore中
```


# 简单使用

```C#
class Program
{
    static void Main(string[] args)
    {
        //调度器,生成实例的时候线程已经开启了，不过是在等待状态
        StdSchedulerFactory factory = new StdSchedulerFactory();
        IScheduler scheduler = factory.GetScheduler().Result;

        //创建一个Job,绑定MyJob
        IJobDetail job = JobBuilder
                            .Create<MyJob>()                     //获取JobBuilder
                            .WithIdentity("jobname1", "group1")  //添加Job的名字和分组
                            .WithDescription("一个简单的任务")     //添加描述
                            .Build();                            //生成IJobDetail

        //创建一个触发器
        ITrigger trigger =
            TriggerBuilder.Create()                                  //获取TriggerBuilder
                            .StartAt(DateBuilder.TodayAt(01, 00, 00))  //开始时间，今天的1点（hh,mm,ss），可使用StartNow()
                            .ForJob(job)                               //将触发器关联给指定的job
                            .WithPriority(10)                          //优先级，当触发时间一样时，优先级大的触发器先执行
                            .WithIdentity("tname1", "group1")          //添加名字和分组
                            .WithSimpleSchedule(x => x.WithIntervalInSeconds(1) //调度，一秒执行一次，执行三次
                                                    .WithRepeatCount(3)
                                                    .Build())
                            .Build();

        //start让调度线程启动【调度线程可以从jobstore中获取快要执行的trigger,然后获取trigger关联的job，执行job】
        scheduler.Start();           
        //将job和trigger注册到scheduler中
        scheduler.ScheduleJob(job, trigger).Wait();
        Console.ReadKey();
    }
}


#region MyJob
/// <summary>
/// 一个简单的Job，所有的Job都要实现IJob接口
/// </summary>
public class MyJob : IJob
{
    public async Task Execute(IJobExecutionContext context)
    {
        await Task.Run(() =>
        {
            Console.WriteLine("hello quartz!");
            //JobDetail的key就是job的分组和job的名字
            Console.WriteLine($"JobDetail的组和名字：{context.JobDetail.Key}"); 
            Console.WriteLine();
        });
    }
}
#endregion
```

# 分模块介绍

Quartz的基本工作流程：scheduler是quartz的独立运行容器，trigger和job都可以注册在scheduler容器中，其中trigger是触发器，用于定义调度任务的时间规则，job是被调度的任务，一个job可以有多个触发器，而一个触发器只能属于一个job。Quartz中一个调度线程QuartzSchedulerThread，调度线程可以找到将要被触发的trigger，通过trigger找到要执行的job，然后在ThreadPool中获取一个线程来执行这个job。JobStore主要作用是存放job和trigger的信息。

## trigger

在Quartz中Trigger的作用是定义Job何时执行。Quartz.net提供了四种触发策略：SimpleSchedule，CalendarIntervalSchedule，DailyTimeIntervalSchedule和CronSchedule。TriggerBuilder顾名思义就是用来创建Trigger的。

### 1. SimpleSchedule

Simpleschedule 是最简单的一种触发策略，它的作用类似于timer，可以设置间隔几秒/几分钟/几小时执行一次，如创建一秒执行一次的触发器如下

```C#
 ITrigger trigger =
        TriggerBuilder.Create()
                        .StartNow()
                        .WithIdentity("tname1", "group1")
                        .WithSimpleSchedule(x => x.WithIntervalInSeconds(1)  //设置时间间隔，时分秒              
                                                .WithRepeatCount(3))       //设置执行次数，总共执行3+1次，
                        .Build();
```

### 2. CalendarIntervalSchedule

CalendarIntervalSchedule扩展了Simplescheduler的功能，Simplescheduler只能在时分秒的维度上指定时间间隔，那么就有一个问题，如果我们想一个月执行一次怎么办呢？要知道每个月的天数是不一样的，用SimpleSchedule实现起来就十分麻烦了。CalendarIntervalSchedule可以实现时分秒天周月年的维度上执行轮询。如创建一个月执行一次的触发器如下：这样

```C#
ITrigger trigger =
    TriggerBuilder.Create()
            .StartAt(DateTimeOffset.Parse("2018/1/6 13:17:00"))
            .WithIdentity("tname1", "group1")
            .WithCalendarIntervalSchedule(x => x.WithIntervalInMonths(1))  //一月执行一次
            .Build();
```

### 3. DailyTimeIntervalSchedule

DailyTimeIntervalSchedule主要用于指定每周的某几天执行，如我们想让每周的周六周日的8:00-20:00，每两秒执行一次，创建触发器如下：

```C#
ITrigger trigger =
    TriggerBuilder.Create()
            .StartAt(DateTimeOffset.Parse("2018/1/6 13:17:00"))
            .WithIdentity("tname1", "group1")
            .WithDailyTimeIntervalSchedule(x => x.OnDaysOfTheWeek(new DayOfWeek[] { DayOfWeek.Saturday, DayOfWeek.Sunday }) //周六和周日
            .StartingDailyAt(TimeOfDay.HourMinuteAndSecondOfDay(8, 00, 00)) //8点开始
            .EndingDailyAt(TimeOfDay.HourMinuteAndSecondOfDay(20, 00, 00))  //20点结束
            .WithIntervalInSeconds(2)                                       //两秒执行一次，可设置时分秒维度
            .WithRepeatCount(3))                                            //一共执行3+1次
            .Build();
```

### 4. CronSchedule

　　CronSchedule是应用最多的触发策略，通过Cron表达是我们可以轻松地表示任意的时间节点，下边的代码创建了一个每隔5秒执行一次的触发器

```C#
ITrigger trigger =
            TriggerBuilder.Create()
                .StartAt(DateTimeOffset.Parse("2018/1/6 13:17:00"))
                .WithIdentity("tname1", "group1")
                .WithCronSchedule("3/5 * * * * ?")  //五秒执行一次
                .Build();
```

> Cron表达式

cron表达式有七个部分组成，以此是秒、分、时、天、月、周、年，其中年是可选的。

| 位置 | 时间域    | 允许值  | 特殊值       |
|----|--------|------|----------------- |
| 1  | 秒      | 0-59 | , - * /          |
| 2  | 分钟     | 0-59 | , - * /         |
| 3  | 小时     | 0-23 | , - * /         |
| 4  | 日期     | 1-31 | , - * ? / L W C |
| 5  | 月份     | 1-12 | , - * /         |
| 6  | 星期     | 1-7  | , - * ? / L C # |
| 7  | 年份（可选） | 1-31 | , - * /       |

星号(*)：可用在所有字段中，表示对应时间域的每一个时刻，例如， 在分钟字段时，表示“每分钟”；

问号（?）：该字符只在日期和星期字段中使用，它通常指定为“无意义的值”，相当于点位符；

减号(-)：表达一个范围，如在小时字段中使用“10-12”，则表示从10到12点，即10,11,12；

逗号(,)：表达一个列表值，如在星期字段中使用“MON,WED,FRI”，则表示星期一，星期三和星期五；

斜杠(/)：x/y表达一个等步长序列，x为起始值，y为增量步长值。如5/15在分钟字段中表示5,20,35,50；

L：该字符只在日期和星期字段中使用，代表“Last”的意思，但它在两个字段中意思不同。L在日期字段中，表示这个月份的最后一天，如一月的31号，非闰年二月的28号；如果L用在星期中，则表示星期六，等同于7。但是，如果L出现在星期字段里，而且在前面有一个数值X，则表示“这个月的最后X天”，例如，6L表示该月的最后星期五；

W：该字符只能出现在日期字段里，是对前导日期的修饰，表示离该日期最近的工作日。例如15W表示离该月15号最近的工作日，如果该月15号是星期六，则匹配14号星期五；如果15日是星期日，则匹配16号星期一；如果15号是星期二，那结果就是15号星期二。但必须注意关联的匹配日期不能够跨月，如你指定1W，如果1号是星期六，结果匹配的是3号星期一，而非上个月最后的那天。W字符串只能指定单一日期，而不能指定日期范围；

LW组合：在日期字段可以组合使用LW，它的意思是当月的最后一个工作日；

井号(#)：该字符只能在星期字段中使用，表示当月某个工作日。如6#3表示当月的第三个星期五(6表示星期五，#3表示当前的第三个)，而4#5表示当月的第五个星期三，假设当月没有第五个星期三，忽略不触发；

Cron表达式对特殊字符的大小写不敏感，对代表星期的缩写英文大小写也不敏感。

| 表示式                      | 说明                                     |
|--------------------------|----------------------------------------|
| 0 0 12 * * ?             | 每天12点运行                                |
| 0 15 10 ? * *            | 每天10:15运行                              |
| 0 15 10 * * ?            | 每天10:15运行                              |
| 0 15 10 * * ? *          | 每天10:15运行                              |
| 0 15 10 * * ? 2008       | 在2008年的每天10：15运行                       |
| 0 * 14 * * ?             | 每天14点到15点之间每分钟运行一次，开始于14:00，结束于14:59。  |
| 0 0/5 14 * * ?           | 每天14点到15点每5分钟运行一次，开始于14:00，结束于14:55。   |
| 0 0/5 14,18 * * ?        | 每天14点到15点每5分钟运行一次，此外每天18点到19点每5钟也运行一次。 |
| 0 0-5 14 * * ?           | 每天14:00点到14:05，每分钟运行一次。                |
| 0 10,44 14 ? 3 WED       | 3月每周三的14:10分和14:44执行。                  |
| 0 15 10 ? * MON-FRI      | 每周一，二，三，四，五的10:15分运行。                  |
| 0 15 10 15 * ?           | 每月15日10:15分运行。                         |
| 0 15 10 L * ?            | 每月最后一天10:15分运行。                        |
| 0 15 10 ? * 6L           | 每月最后一个星期五10:15分运行。                     |
| 0 15 10 ? * 6L 2007-2009 | 在2007,2008,2009年每个月的最后一个星期五的10:15分运行。  |
| 0 15 10 ? * 6#3          | 每月第三个星期五的10:15分运行。                     |

### Calendar

通过上边的介绍，我们知道通过触发器Trigger可以设置Job的执行时间，但是有时候只使用Trigger来调度比较麻烦，如一年中每天都执行，但是元旦、圣诞节和情人节这三天不执行。使用trigger也可以实现，但是比较麻烦，如果我们有一种方法可以方便地排除这三天就好办了，Calendar主要作用就是为了排除Trigger中一些特定的时间节点。看一个简单的栗子：


```C#
class Program
{
    static void Main(string[] args)
    {
        //调度器
        IScheduler scheduler = StdSchedulerFactory.GetDefaultScheduler().Result;
        //JobDetail
        IJobDetail job = JobBuilder
                            .Create<MyJob>()
                            .Build();
        //获取一个Calendar实例
        DailyCalendar calendar = new DailyCalendar(DateBuilder.DateOf(19, 0, 0).DateTime, DateBuilder.DateOf(23, 0, 0).DateTime);//21~23点不执行
        //将Calendar注册到Scheduler中
        scheduler.AddCalendar("myCalendar", calendar, true, true);//参数依次是:calendarname,calendar,是否替换同名clendar,是否更新trigger
        //获取一个触发器，并将calendar绑定到触发器上
        ITrigger trigger =
                TriggerBuilder.Create()
                    .StartNow()
                    .WithIdentity("tname1", "group1")
                    .WithCronSchedule("0/2 * * * * ?")  //2秒执行一次
                    .ModifiedByCalendar("myCalendar")   //把Calendar绑定到trigger
                    .Build();

        //start让调度线程启动
        scheduler.Start();
        //将job添加到调度器中，同时将trigger绑定到job
        scheduler.ScheduleJob(job, trigger).Wait();
        Console.ReadKey();
    }
}

#region MyJob，继承IJob接口
/// <summary>
/// 一个简单的Job
/// </summary>
public class MyJob : IJob
{public Task Execute(IJobExecutionContext context)
    {
        return Task.Run(() =>
        {
            Console.WriteLine($"触发时间：{context.ScheduledFireTimeUtc?.LocalDateTime},下次触发时间：{context.NextFireTimeUtc?.LocalDateTime}");
        });
    }

}
#endregion
```

使用Calendar的流程是：首先获取一个Calendar实例，然后将Calendar注册到scheduler容器中，在将Calendar绑定到触发器上即可。Quartz.net中一共提供了六种Calendar，六种Calendar的用法大同小异，列举如下：

```C#
////【1】.DailyCalendar 用于排除一天中的某一段时间
DailyCalendar calendar = new DailyCalendar(DateBuilder.DateOf(19, 0, 0).DateTime, DateBuilder.DateOf(23, 0, 0).DateTime);//21~23点不执行


////【2】.WeeklyCalendar 用于排除一周中的某几天
WeeklyCalendar calendar = new WeeklyCalendar();
calendar.SetDayExcluded(DayOfWeek.Sunday, true);//周日不执行 
//注：如果想让周日恢复执行，执行代码：  calendar.SetDayExcluded(DayOfWeek.Sunday, false);

////【3】.HolidayCalendar 用于排除某些日期
HolidayCalendar calendar = new HolidayCalendar();
calendar.AddExcludedDate(DateTime.Parse("2018/1/2")); //2018年1月2号不执行
//注：如果想让2019/1/9恢复执行，执行代码：  calendar.RemoveExcludedDate(DateTime.Parse("2018/1/2"));

////【4】.MonthlyCalendar 用于排除每个月的某天*************************************
MonthlyCalendar calendar = new MonthlyCalendar();
calendar.SetDayExcluded(8,true); //每个月的8号不执行
//注：如果想让8号恢复执行，执行代码：  calendar.SetDayExcluded(8, false);

////【5】AnnualCalendar 用于排除一年中的某些天*************************************
AnnualCalendar calendar = new AnnualCalendar();
calendar.SetDayExcluded(DateTime.Parse("2018/1/2"), true);//每年1月2号不执行
//注：如果想让1月8号恢复执行，执行代码：   calendar.SetDayExcluded(DateTime.Parse("2018/1/2"),true);

////【6】.CronCalendar 用于排除cron表达式表示的时间***************************
CronCalendar calendar = new CronCalendar("* * * 2 1 ?"); //每年的1月2号不执行
```


## scheduler

调度器scheduler是Quartz中的独立工作容器，所有的Trigger和Job都需要注册到scheduler中才能工作。我们可以通过SchedulerFactory来获取scheduler实例。如下：

```C#
//1.获取默认的标准Scheduler引用
IScheduler scheduler = StdSchedulerFactory.GetDefaultScheduler().Result;


//2.通过代码配置scheduler
 NameValueCollection properties = new NameValueCollection
        {
            //scheduler的名字
            ["quartz.scheduler.instanceName"] = "MyScheduler",
            // 设置线程池中线程个数为20个
            ["quartz.threadPool.threadCount"] = "20",
            ["quartz.threadPool.type"] = "Quartz.Simpl.SimpleThreadPool, Quartz",
            //JobStore类型为内存存储
            ["quartz.jobStore.type"] = "Quartz.Simpl.RAMJobStore, Quartz"
        };
        ISchedulerFactory factroy = new StdSchedulerFactory(properties);
        IScheduler scheduler= await factroy .GetScheduler();
```

这里列一些会经常用的到方法，方法比较简单直观，就不一一展示了。

```C#
scheduler.PauseJob(JobKey.Create("jobname", "groupname"));//暂停job
scheduler.ResumeJob(JobKey.Create("jobname", "groupname"));//重新启动job
scheduler.DeleteJob(JobKey.Create("jobname", "groupname"));//删除job
scheduler.PauseTrigger(new TriggerKey("triggername", "groupname"));//暂停trigger
scheduler.ResumeTrigger(new TriggerKey("triggername", "groupname"));//重新启动trigger
scheduler.UnscheduleJob(new TriggerKey("triggername", "groupname"));//删除trigger
scheduler.GetTriggersOfJob(JobKey.Create("jobname", "groupname"));//获取一个job的所有key    
scheduler.Standby();  //暂停所有的触发器，可通过shceduler.Start()重启
scheduler.Shutdown(); //关闭scheduler，释放资源。通过Shutdown()关闭后，不能通过Start()重启
scheduler.GetMetaData();//获取scheduler的元数据
scheduler.Clear();//清空容器中所有的IJob,ITrigger

//调度多个任务
Dictionary<IJobDetail, IReadOnlyCollection<ITrigger>> triggersAndJobs = new Dictionary<IJobDetail, IReadOnlyCollection<ITrigger>>();
triggersAndJobs.Add(job1, new List<ITrigger>() { trigger1,trigger2});
triggersAndJobs.Add(job2, new List<ITrigger>() { trigger3});
await scheduler.ScheduleJobs(triggersAndJobs, true);
```

# Listener介绍

　　TriggerListener和JobListener用法类似，这里以JobListener为例来介绍Quartz中的Listener。JobListener用于在Job执行前、后和被拒绝时执行一些动作，和Asp.net中的filter很相似，用法并不复杂，看一个简单的栗子：

```C#
class Program
{
    static void Main(string[] args)
    {
        //获取调度器
        NameValueCollection pairs = new NameValueCollection() { { "quartz.threadPool.ThreadCount", "30" } };
        StdSchedulerFactory factory = new StdSchedulerFactory(pairs);
        IScheduler scheduler = factory.GetScheduler().Result; 

        //创建Job
        IJobDetail job = JobBuilder
                .Create<MyJob>()                     //获取JobBuilder
                .WithIdentity("jobname1", "group1")  //添加Job的名字和分组
                .Build();                            //生成IJobDetail


        //创建rigger
        ITrigger trigger =
            TriggerBuilder.Create()                                  //获取JobBuilder
                .StartAt(DateBuilder.TodayAt(01, 00, 00))  //开始时间，今天的1点（hh,mm,ss），可使用StartNow()
                .WithPriority(10)                          //优先级，当触发时间一样时，优先级大的触发器先执行
                .WithIdentity("tname1", "group1")          //添加名字和分组
                .WithSimpleSchedule(x => x.WithIntervalInSeconds(1)
                                        .RepeatForever()
                                        .Build())
                .Build();

        //启动调度器
        scheduler.Start();
        
        //myJobListener监控所有的job
        scheduler.ListenerManager.AddJobListener(new MyJobListener(), GroupMatcher<JobKey>.AnyGroup());
        //将job添加到调度器中，同时将trigger绑定到job
        scheduler.ScheduleJob(job, trigger).Wait();
        Console.ReadKey();
    }
}


#region MyJob，继承IJob接口
/// <summary>
/// 一个简单的Job
/// </summary>
public class MyJob : IJob
{
    public async Task Execute(IJobExecutionContext context)
    {
        await Task.Run(() =>
        {
            Console.WriteLine("hello quartz!");
            Console.WriteLine($"ThreadPool中的线程个数：{context.Scheduler.GetMetaData().Result.ThreadPoolSize}");
        });
    }
}
#endregion

#region myJobListener，继承IJobListener接口
/// <summary>
/// 一个简单的JobListener,triggerListener类似
/// </summary>
public class MyJobListener : IJobListener
{
    public string Name => "hello joblisener";
    //job被拒绝时执行
    public async Task JobExecutionVetoed(IJobExecutionContext context, CancellationToken cancellationToken = default(CancellationToken))
    {
        await Task.Run(() => { });
    }
    //job开始前执行
    public async Task JobToBeExecuted(IJobExecutionContext context, CancellationToken cancellationToken = default(CancellationToken))
    {
        await Task.Run(() =>
        {
            Console.WriteLine("myjob-------------begin");
        });
    }
    //job完成后执行
    public async Task JobWasExecuted(IJobExecutionContext context, JobExecutionException jobException, CancellationToken cancellationToken = default(CancellationToken))
    {
        await Task.Run(() =>
        {
            Console.WriteLine("myjob---------------end");　　　　　　　　　 Console.WriteLine();
        });
    }
    #endregion
}
```
上边例子中，Listener执行的动作很简单，在Job执行前打印begin，执行后打印end，在实际开发中，我们可以在通过Listenter来记录job的执行日志

