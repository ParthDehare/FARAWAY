import { useCallback, useRef } from "react";
import { useAlertStore } from "@/stores/alertStore";
import { useMapStore } from "@/stores/mapStore";

export function useRedAlert() {
  const { triggerRedAlert, dismissRedAlert, redAlertActive } = useAlertStore();
  const { flyTo } = useMapStore();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const timelineRef = useRef<any>(null);

  const trigger = useCallback(
    (alertId: string, location?: [number, number]) => {
      triggerRedAlert(alertId);
      if (location) flyTo(location, 14);
    },
    [triggerRedAlert, flyTo]
  );

  const dismiss = useCallback(() => {
    dismissRedAlert();
    timelineRef.current?.kill();
  }, [dismissRedAlert]);

  return { redAlertActive, trigger, dismiss, timelineRef };
}
