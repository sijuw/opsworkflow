import { Link } from "react-router-dom";

function WorkflowCard({
  title,
  description,
  icon: Icon,
  status = "planned",
  to,
}) {
  const isAvailable = status === "available";

  // Shared CSS classes for the card wrapper
  const cardClasses = `group relative flex cursor-pointer flex-col justify-between rounded-2xl border-2 bg-white dark:bg-slate-900 p-6 transition-all duration-300 hover:-translate-y-1 hover:shadow-lg ${
    isAvailable
      ? "border-transparent dark:border-transparent hover:border-[#007cc2] dark:hover:border-[#007cc2] shadow-sm"
      : "border-slate-100 dark:border-slate-800 opacity-60 hover:opacity-100 hover:border-slate-300 dark:hover:border-slate-700"
  }`;

  // The internal content of the card
  const CardContent = (
    <div>
      <div className="flex items-start justify-between">
        {/* Bigger, rounded square icon container */}
        <div
          className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl transition-transform duration-300 group-hover:scale-110 ${
            isAvailable
              ? "bg-[#007cc2]/10 text-[#007cc2] dark:bg-[#007cc2]/20 dark:text-[#3399ff]"
              : "bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400"
          }`}
        >
          <Icon className="h-7 w-7" />
        </div>

        {/* Dynamic Status Badge */}
        <div
          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
            isAvailable
              ? "bg-green-100 text-green-700 dark:bg-green-500/10 dark:text-green-400"
              : "bg-yellow-100 text-yellow-700 dark:bg-yellow-500/10 dark:text-yellow-400"
          }`}
        >
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              isAvailable ? "bg-green-500" : "bg-yellow-500"
            }`}
          ></span>
          {isAvailable ? "Available" : "Planned"}
        </div>
      </div>

      <div className="mt-5">
        <h3
          className={`text-lg font-semibold ${
            isAvailable 
              ? "text-slate-900 dark:text-slate-100" 
              : "text-slate-700 dark:text-slate-300"
          }`}
        >
          {title}
        </h3>
        <p className="mt-2 text-sm leading-relaxed text-slate-500 dark:text-slate-400">
          {description}
        </p>
      </div>
    </div>
  );

  // If available and has a route, wrap in a Link. Otherwise, standard div.
  if (isAvailable && to) {
    return (
      <Link to={to} className={cardClasses}>
        {CardContent}
      </Link>
    );
  }

  return <div className={cardClasses}>{CardContent}</div>;
}

export default WorkflowCard;