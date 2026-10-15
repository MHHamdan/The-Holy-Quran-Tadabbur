import { useLanguageStore } from '../stores/languageStore';
import { HubPage } from '../components/layout/HubPage';
import { HubGrid } from '../components/layout/HubGrid';
import { MEMORISE_ITEMS } from '../components/layout/navConfig';

export function MemoriseHubPage() {
  const { language } = useLanguageStore();
  return (
    <HubPage titleKey="hub_memorise_title" subtitleKey="hub_memorise_subtitle">
      <HubGrid items={MEMORISE_ITEMS} language={language} />
    </HubPage>
  );
}

export default MemoriseHubPage;
