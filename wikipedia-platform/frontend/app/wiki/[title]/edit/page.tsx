import EditArticleForm from "@/components/EditArticleForm";
import { pathToTitle } from "@/lib/api";

type EditPageProps = {
  params: {
    title: string;
  };
};

export default function EditPage({ params }: EditPageProps) {
  return (
    <main className="content-page wide">
      <EditArticleForm title={pathToTitle(params.title)} />
    </main>
  );
}

