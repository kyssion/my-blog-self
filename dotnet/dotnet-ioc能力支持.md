1. dotnet ioc能力

```c#
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

namespace test_ioc;

class Program
{
    static void Main(string[] args)
    {
        HostApplicationBuilder builder = Host.CreateApplicationBuilder(args);
        // 注册生命周期是每次获取都生成新的的模式
        builder.Services.AddTransient<IExampleTransientService, ExampleTransientService>();
        // 注册生命周期是每次重新获取就会改变的模式
        builder.Services.AddScoped<IExampleScopedService, ExampleScopedService>();
        // 获取单例
        builder.Services.AddSingleton<IExampleSingletonService, ExampleSingletonService>();
        // 注意这里 , 如果这里生命周期会忽略低级的
        builder.Services.AddTransient<ServiceLifetimeReporter>();
        using IHost host = builder.Build();

        ExemplifyServiceLifetime(host.Services, "Lifetime 1");
        ExemplifyServiceLifetime(host.Services, "Lifetime 2");
        host.Run();
    }
    
    static void ExemplifyServiceLifetime(IServiceProvider hostProvider, string lifetime)
    {
        using IServiceScope serviceScope = hostProvider.CreateScope();
        IServiceProvider provider = serviceScope.ServiceProvider;
        ServiceLifetimeReporter logger = provider.GetRequiredService<ServiceLifetimeReporter>();
        logger.ReportServiceLifetimeDetails(
            $"{lifetime}: Call 1 to provider.GetRequiredService<ServiceLifetimeReporter>()");

        Console.WriteLine("...");

        logger = provider.GetRequiredService<ServiceLifetimeReporter>();
        logger.ReportServiceLifetimeDetails(
            $"{lifetime}: Call 2 to provider.GetRequiredService<ServiceLifetimeReporter>()");

        Console.WriteLine();
    }
}

public interface IReportServiceLifetime
{
    Guid Id { get; }

    ServiceLifetime Lifetime { get; }
}

public interface IExampleTransientService : IReportServiceLifetime
{
    ServiceLifetime IReportServiceLifetime.Lifetime => ServiceLifetime.Transient;
}

public interface IExampleSingletonService : IReportServiceLifetime
{
    ServiceLifetime IReportServiceLifetime.Lifetime => ServiceLifetime.Singleton;
}

public interface IExampleScopedService : IReportServiceLifetime
{
    ServiceLifetime IReportServiceLifetime.Lifetime => ServiceLifetime.Scoped;
}

internal sealed class ExampleTransientService : IExampleTransientService
{
    Guid IReportServiceLifetime.Id { get; } = Guid.NewGuid();
}

internal sealed class ExampleScopedService : IExampleScopedService
{
    Guid IReportServiceLifetime.Id { get; } = Guid.NewGuid();
}

internal sealed class ExampleSingletonService : IExampleSingletonService
{
    Guid IReportServiceLifetime.Id { get; } = Guid.NewGuid();
}

internal sealed class ServiceLifetimeReporter(
    IExampleTransientService transientService,
    IExampleScopedService scopedService,
    IExampleSingletonService singletonService)
{
    public void ReportServiceLifetimeDetails(string lifetimeDetails)
    {
        Console.WriteLine(lifetimeDetails);

        LogService(transientService, "Always different");
        LogService(scopedService, "Changes only with lifetime");
        LogService(singletonService, "Always the same");
    }

    private static void LogService<T>(T service, string message)
        where T : IReportServiceLifetime =>
        Console.WriteLine(
            $"    {typeof(T).Name}: {service.Id} ({message})");
}
```

简答说: 生命周期三种类型
1. Transient 每次从 provider 后去数据都是新的
2. Scope 每次从 scope 中获取都是新的
3. Singleton 不生成新的

注意被注入的对象如果生命周期大于内部注入的对象,那么注入的对象的生命周期将会和被注入的一致