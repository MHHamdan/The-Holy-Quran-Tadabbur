import { useLanguageStore } from '../stores/languageStore';
import { HubPage } from '../components/layout/HubPage';
import { HubGrid } from '../components/layout/HubGrid';
import { EXPLORE_ITEMS } from '../components/layout/navConfig';

export function ExploreHubPage() {
  const { language } = useLanguageStore();
  return (
    <HubPage titleKey="hub_explore_title" subtitleKey="hub_explore_subtitle">
      <HubGrid items={EXPLORE_ITEMS} language={language} />
    </HubPage>
  );
}

export default ExploreHubPage;
