import { useMemo, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import {
  ArrowRight,
  BracketsCurly,
  CaretLeft,
  CaretRight,
  ChartLineUp,
  ChatCircleText,
  ClockCounterClockwise,
  Database,
  DotsThree,
  FileText,
  FolderOpen,
  Gauge,
  GitBranch,
  Link as LinkIcon,
  LockKey,
  PaperPlaneTilt,
  Plugs,
  Plus,
  Rows,
  ShieldCheck,
  SignOut,
  Stack,
  UserCircle,
} from "@phosphor-icons/react"

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyTitle } from "@/components/ui/empty"
import { Field, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

import "./App.css"

type View = "landing" | "login" | "workspace"

type Project = {
  id: string
  name: string
  phase: string
  agent: string
  createdAt: string
}

type Message = {
  id: string
  role: "pm" | "operator"
  content: string
}

const sampleArtifacts = [
  { name: "PRD", status: "Awaiting scope" },
  { name: "Evaluation criteria", status: "Not created" },
  { name: "Implementation plan", status: "Not created" },
]

const suggestions = [
  "Scope a new LLM support agent for a client",
  "Turn my discovery notes into a PRD",
  "Define success criteria before architecture",
]

function App() {
  const [view, setView] = useState<View>("landing")
  const [project, setProject] = useState<Project | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [draft, setDraft] = useState("")
  const [rightRailOpen, setRightRailOpen] = useState(true)

  const projectTitle = useMemo(() => {
    if (!draft.trim()) return "New client application"
    const words = draft.trim().split(/\s+/).slice(0, 7).join(" ")
    return words.charAt(0).toUpperCase() + words.slice(1)
  }, [draft])

  function startProject(seed?: string) {
    const source = seed ?? draft
    const name =
      source.trim().length > 0
        ? source.trim().split(/\s+/).slice(0, 7).join(" ")
        : "New client application"

    setProject({
      id: "thread-local-001",
      name: name.charAt(0).toUpperCase() + name.slice(1),
      phase: "Scoping",
      agent: "Project Manager",
      createdAt: "local draft",
    })
    setMessages([
      {
        id: "pm-open",
        role: "pm",
        content:
          "Recommend starting with scope boundaries and evaluation criteria. Give me the product idea, target users, constraints, and what a passing result should prove.",
      },
    ])
    setDraft("")
    setRightRailOpen(true)
  }

  function sendMessage() {
    const value = draft.trim()
    if (!value) return

    if (!project) {
      startProject(value)
      setDraft("")
      return
    }

    setMessages((current) => [
      ...current,
      { id: `operator-${current.length}`, role: "operator", content: value },
      {
        id: `pm-${current.length}`,
        role: "pm",
        content:
          "Captured. I will keep this as scope signal until the PRD is ready for evaluation design. Next useful detail: who signs off on success and which failures are unacceptable.",
      },
    ])
    setDraft("")
  }

  return (
    <TooltipProvider delayDuration={150}>
      <AnimatePresence mode="wait">
        {view === "landing" && <LandingPage key="landing" onEnter={() => setView("login")} />}
        {view === "login" && <LoginPage key="login" onBack={() => setView("landing")} onLogin={() => setView("workspace")} />}
        {view === "workspace" && (
          <Workspace
            key="workspace"
            draft={draft}
            messages={messages}
            project={project}
            projectTitle={projectTitle}
            rightRailOpen={rightRailOpen}
            onDraftChange={setDraft}
            onSend={sendMessage}
            onSignOut={() => {
              setView("landing")
              setProject(null)
              setMessages([])
              setDraft("")
            }}
            onStartProject={startProject}
            onToggleRightRail={() => setRightRailOpen((open) => !open)}
          />
        )}
      </AnimatePresence>
    </TooltipProvider>
  )
}

function LandingPage({ onEnter }: { onEnter: () => void }) {
  return (
    <motion.main
      className="min-h-dvh bg-background text-foreground"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.35 }}
    >
      <section className="landing-hero">
        <img
          className="landing-hero__image"
          src="https://picsum.photos/seed/meta-harness-operator-room/1800/1200"
          alt="A quiet workroom prepared for project review"
        />
        <div className="landing-hero__shade" />
        <nav className="landing-nav" aria-label="Primary">
          <div className="brand-mark">
            <span className="brand-mark__glyph">MH</span>
            <span>Meta Harness</span>
          </div>
          <div className="landing-nav__actions">
            <Button variant="ghost" onClick={onEnter}>
              Sign in
            </Button>
            <Button onClick={onEnter}>
              Open cockpit
              <ArrowRight data-icon="inline-end" />
            </Button>
          </div>
        </nav>

        <div className="landing-copy">
          <Badge variant="secondary">Agent application studio</Badge>
          <h1>Project-scoped agent work, visible from first brief to final eval.</h1>
          <p>
            Meta Harness gives the operator one place to scope work with the PM, inspect earned artifacts, and hand off to LangSmith only when raw trajectories matter.
          </p>
          <div className="landing-copy__actions">
            <Button size="lg" onClick={onEnter}>
              Start with the PM
              <ArrowRight data-icon="inline-end" />
            </Button>
            <Button size="lg" variant="outline" asChild>
              <a href="#product-surface">View product surface</a>
            </Button>
          </div>
        </div>
      </section>

      <section id="product-surface" className="landing-section">
        <div className="landing-section__heading">
          <Badge variant="outline">Stripe-family pass</Badge>
          <h2>Calm for stakeholders. Dense when the operator needs leverage.</h2>
        </div>
        <Tabs defaultValue="cockpit" className="landing-tabs">
          <TabsList>
            <TabsTrigger value="cockpit">Operator cockpit</TabsTrigger>
            <TabsTrigger value="portal">Stakeholder portal</TabsTrigger>
          </TabsList>
          <TabsContent value="cockpit">
            <div className="surface-proof">
              <div>
                <p className="eyebrow">Cockpit signal</p>
                <h3>PM chat is the entry point. Artifacts earn their place.</h3>
              </div>
              <div className="surface-proof__grid">
                <SignalTile label="Active agent" value="Project Manager" icon={<UserCircle weight="duotone" />} />
                <SignalTile label="Current phase" value="Scoping" icon={<GitBranch weight="duotone" />} />
                <SignalTile label="Artifact store" value="Filesystem" icon={<FolderOpen weight="duotone" />} />
              </div>
            </div>
          </TabsContent>
          <TabsContent value="portal">
            <div className="surface-proof">
              <div>
                <p className="eyebrow">Broadcast mode</p>
                <h3>Stakeholders read the PM narrative. The operator remains the channel.</h3>
              </div>
              <div className="surface-proof__grid">
                <SignalTile label="PRD package" value="Read only" icon={<FileText weight="duotone" />} />
                <SignalTile label="Eval summary" value="Distilled" icon={<ChartLineUp weight="duotone" />} />
                <SignalTile label="Trace detail" value="LangSmith" icon={<LinkIcon weight="duotone" />} />
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </section>
    </motion.main>
  )
}

function SignalTile({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) {
  return (
    <div className="signal-tile">
      <div className="signal-tile__icon">{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function LoginPage({ onBack, onLogin }: { onBack: () => void; onLogin: () => void }) {
  return (
    <motion.main
      className="login-shell bg-background text-foreground"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      transition={{ duration: 0.28 }}
    >
      <Button className="login-back" variant="ghost" onClick={onBack}>
        <CaretLeft data-icon="inline-start" />
        Back
      </Button>
      <Card className="login-card">
        <CardHeader>
          <div className="login-card__icon">
            <LockKey weight="duotone" />
          </div>
          <CardTitle>Enter the cockpit</CardTitle>
          <CardDescription>Use the operator seat for project creation, PM chat, approvals, artifacts, and eval review.</CardDescription>
        </CardHeader>
        <CardContent>
          <FieldGroup>
            <Field>
              <FieldLabel htmlFor="email">Email</FieldLabel>
              <Input id="email" type="email" placeholder="operator@company.com" defaultValue="jason@metaharness.local" />
              <FieldDescription>Local mock auth for this frontend pass.</FieldDescription>
            </Field>
            <Field>
              <FieldLabel htmlFor="password">Password</FieldLabel>
              <Input id="password" type="password" defaultValue="metaharness" />
            </Field>
          </FieldGroup>
        </CardContent>
        <CardFooter className="flex flex-col gap-3">
          <Button className="w-full" size="lg" onClick={onLogin}>
            Continue
            <ArrowRight data-icon="inline-end" />
          </Button>
          <p className="text-sm text-muted-foreground">Auth provider decision is still pending. This screen preserves the intended seat boundary.</p>
        </CardFooter>
      </Card>
    </motion.main>
  )
}

function Workspace({
  draft,
  messages,
  project,
  projectTitle,
  rightRailOpen,
  onDraftChange,
  onSend,
  onSignOut,
  onStartProject,
  onToggleRightRail,
}: {
  draft: string
  messages: Message[]
  project: Project | null
  projectTitle: string
  rightRailOpen: boolean
  onDraftChange: (value: string) => void
  onSend: () => void
  onSignOut: () => void
  onStartProject: (seed?: string) => void
  onToggleRightRail: () => void
}) {
  return (
    <motion.div
      className="workspace-shell bg-background text-foreground"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.25 }}
    >
      <WorkspaceSidebar project={project} onStartProject={onStartProject} onSignOut={onSignOut} />
      <main className="workspace-main">
        <WorkspaceHeader project={project} onToggleRightRail={onToggleRightRail} />
        <ScrollArea className="workspace-scroll">
          <section className="workspace-content">
            <PipelineStrip project={project} />
            <PMThread
              draft={draft}
              messages={messages}
              project={project}
              projectTitle={projectTitle}
              onDraftChange={onDraftChange}
              onSend={onSend}
              onStartProject={onStartProject}
            />
          </section>
        </ScrollArea>
      </main>
      <ProjectRail open={rightRailOpen} project={project} onToggle={onToggleRightRail} />
    </motion.div>
  )
}

function WorkspaceSidebar({
  project,
  onStartProject,
  onSignOut,
}: {
  project: Project | null
  onStartProject: () => void
  onSignOut: () => void
}) {
  return (
    <aside className="workspace-sidebar">
      <div className="workspace-sidebar__top">
        <div className="brand-mark">
          <span className="brand-mark__glyph">MH</span>
          <span>Meta Harness</span>
        </div>
        <Button className="w-full justify-start" variant="outline" onClick={() => onStartProject()}>
          <Plus data-icon="inline-start" />
          New project thread
        </Button>
        <nav className="sidebar-nav" aria-label="Workspace">
          <a className="sidebar-nav__item sidebar-nav__item--active" href="#projects">
            <FolderOpen weight="duotone" />
            Projects
          </a>
          <a className="sidebar-nav__item" href="#integrations">
            <Plugs weight="duotone" />
            Integrations
          </a>
          <a className="sidebar-nav__item" href="#datasets">
            <Database weight="duotone" />
            Datasets
          </a>
          <a className="sidebar-nav__item" href="#observability">
            <Gauge weight="duotone" />
            Observability
          </a>
        </nav>
      </div>

      <div className="workspace-sidebar__bottom">
        <div className="sidebar-project">
          <span className="text-xs text-muted-foreground">Active project</span>
          <strong>{project?.name ?? "None yet"}</strong>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button className="w-full justify-between" variant="ghost">
              <span className="inline-flex items-center gap-2">
                <Avatar className="size-7">
                  <AvatarFallback>JA</AvatarFallback>
                </Avatar>
                Jason
              </span>
              <DotsThree />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-56">
            <DropdownMenuLabel>Operator seat</DropdownMenuLabel>
            <DropdownMenuGroup>
              <DropdownMenuItem>
                <UserCircle />
                Account
              </DropdownMenuItem>
              <DropdownMenuItem>
                <ShieldCheck />
                Access model
              </DropdownMenuItem>
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={onSignOut}>
              <SignOut />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </aside>
  )
}

function WorkspaceHeader({ project, onToggleRightRail }: { project: Project | null; onToggleRightRail: () => void }) {
  return (
    <header className="workspace-header">
      <div>
        <p className="eyebrow">Developer cockpit</p>
        <h1>{project ? project.name : "PM blank slate"}</h1>
      </div>
      <div className="workspace-header__actions">
        <Dialog>
          <DialogTrigger asChild>
            <Button variant="outline">
              <Rows data-icon="inline-start" />
              Project model
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Project threads are project objects</DialogTitle>
              <DialogDescription>
                Each new thread maps to a project id. Agent artifacts live in the backend filesystem and become navigable once produced.
              </DialogDescription>
            </DialogHeader>
          </DialogContent>
        </Dialog>
        <Sheet>
          <SheetTrigger asChild>
            <Button className="lg:hidden" variant="outline">
              <Stack data-icon="inline-start" />
              Project rail
            </Button>
          </SheetTrigger>
          <SheetContent side="right">
            <SheetHeader>
              <SheetTitle>Project rail</SheetTitle>
              <SheetDescription>Artifacts, datasets, and LangSmith links for the active project.</SheetDescription>
            </SheetHeader>
            <div className="sheet-rail-content">
              {project ? <ProjectRailDetails project={project} /> : <ProjectRailEmpty />}
            </div>
          </SheetContent>
        </Sheet>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button className="hidden lg:inline-flex" variant="ghost" size="icon" onClick={onToggleRightRail}>
              <Stack />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Toggle project rail</TooltipContent>
        </Tooltip>
      </div>
    </header>
  )
}

function PipelineStrip({ project }: { project: Project | null }) {
  const progress = project ? 12 : 0

  return (
    <section className="pipeline-strip" aria-label="Pipeline state">
      <div className="pipeline-strip__summary">
        <Badge variant={project ? "secondary" : "outline"}>{project ? project.phase : "No thread"}</Badge>
        <div>
          <strong>{project ? project.agent : "Project Manager waiting"}</strong>
          <span>{project ? "Thread is open. Scope signal is being collected." : "Create a project thread to begin."}</span>
        </div>
      </div>
      <div className="pipeline-strip__progress">
        <Progress value={progress} />
        <span>{progress}% earned</span>
      </div>
    </section>
  )
}

function PMThread({
  draft,
  messages,
  project,
  projectTitle,
  onDraftChange,
  onSend,
  onStartProject,
}: {
  draft: string
  messages: Message[]
  project: Project | null
  projectTitle: string
  onDraftChange: (value: string) => void
  onSend: () => void
  onStartProject: (seed?: string) => void
}) {
  return (
    <section className="pm-thread">
      <div className="pm-thread__header">
        <div>
          <p className="eyebrow">Project Manager</p>
          <h2>{project ? "Scope the work." : "Start with the first useful brief."}</h2>
        </div>
        <Badge variant="outline">{project ? project.id : "New thread = new project"}</Badge>
      </div>

      {project ? (
        <div className="message-stack">
          {messages.map((message) => (
            <motion.article
              layout
              key={message.id}
              className={message.role === "pm" ? "message message--pm" : "message message--operator"}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <span>{message.role === "pm" ? "PM" : "Operator"}</span>
              <p>{message.content}</p>
            </motion.article>
          ))}
        </div>
      ) : (
        <Empty className="blank-empty">
          <EmptyHeader>
            <EmptyTitle>Nothing is running yet.</EmptyTitle>
            <EmptyDescription>
              The PM will create the first project thread from your brief. Artifacts and evals stay empty until the agent writes them.
            </EmptyDescription>
          </EmptyHeader>
          <EmptyContent>
            <div className="suggestion-row">
              {suggestions.map((suggestion) => (
                <Button key={suggestion} variant="outline" onClick={() => onStartProject(suggestion)}>
                  {suggestion}
                </Button>
              ))}
            </div>
          </EmptyContent>
        </Empty>
      )}

      <div className="composer">
        <div className="composer__meta">
          <span>{project ? "Thread input" : `Draft title: ${projectTitle}`}</span>
          <span>PM only</span>
        </div>
        <Textarea
          value={draft}
          onChange={(event) => onDraftChange(event.target.value)}
          placeholder="Describe the client idea, constraints, users, and the standard of proof..."
          onKeyDown={(event) => {
            if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
              onSend()
            }
          }}
        />
        <div className="composer__footer">
          <span>Command Enter sends. The backend stream will replace this local mock state.</span>
          <Button onClick={onSend}>
            {project ? "Send" : "Create project"}
            <PaperPlaneTilt data-icon="inline-end" />
          </Button>
        </div>
      </div>
    </section>
  )
}

function ProjectRail({ open, project, onToggle }: { open: boolean; project: Project | null; onToggle: () => void }) {
  return (
    <aside className={open ? "project-rail project-rail--open" : "project-rail"}>
      <button className="project-rail__toggle" type="button" onClick={onToggle} aria-label="Toggle project rail">
        {open ? <CaretRight /> : <CaretLeft />}
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            className="project-rail__content"
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 12 }}
            transition={{ duration: 0.18 }}
          >
            <div className="project-rail__header">
              <p className="eyebrow">Project rail</p>
              <h2>{project ? "Earned project signal" : "No project selected"}</h2>
            </div>
            {project ? <ProjectRailDetails project={project} /> : <ProjectRailEmpty />}
          </motion.div>
        )}
      </AnimatePresence>
    </aside>
  )
}

function ProjectRailEmpty() {
  return (
    <div className="rail-empty">
      <Skeleton className="h-3 w-28" />
      <Skeleton className="h-24 w-full" />
      <p>Artifacts, eval datasets, handoff logs, and LangSmith links appear after a project thread exists.</p>
    </div>
  )
}

function ProjectRailDetails({ project }: { project: Project }) {
  return (
    <Accordion type="multiple" defaultValue={["artifacts", "evals", "links"]} className="rail-accordion">
      <AccordionItem value="artifacts">
        <AccordionTrigger>
          <span className="rail-trigger">
            <FolderOpen weight="duotone" />
            Artifacts
          </span>
        </AccordionTrigger>
        <AccordionContent>
          <div className="rail-list">
            {sampleArtifacts.map((artifact) => (
              <div className="rail-row" key={artifact.name}>
                <FileText weight="duotone" />
                <div>
                  <strong>{artifact.name}</strong>
                  <span>{artifact.status}</span>
                </div>
              </div>
            ))}
          </div>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="evals">
        <AccordionTrigger>
          <span className="rail-trigger">
            <ChartLineUp weight="duotone" />
            Eval data
          </span>
        </AccordionTrigger>
        <AccordionContent>
          <div className="rail-list">
            <div className="rail-row">
              <Database weight="duotone" />
              <div>
                <strong>Public dataset</strong>
                <span>Not generated</span>
              </div>
            </div>
            <div className="rail-row">
              <BracketsCurly weight="duotone" />
              <div>
                <strong>Held-out set</strong>
                <span>Cockpit-only once available</span>
              </div>
            </div>
          </div>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="links">
        <AccordionTrigger>
          <span className="rail-trigger">
            <LinkIcon weight="duotone" />
            LangSmith
          </span>
        </AccordionTrigger>
        <AccordionContent>
          <div className="rail-list">
            <a className="rail-link" href="https://smith.langchain.com/" target="_blank" rel="noreferrer">
              Open LangSmith
              <ArrowRight />
            </a>
            <p className="rail-note">Raw traces stay outside Meta Harness. This rail keeps the handoff explicit.</p>
          </div>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="history">
        <AccordionTrigger>
          <span className="rail-trigger">
            <ClockCounterClockwise weight="duotone" />
            Handoff log
          </span>
        </AccordionTrigger>
        <AccordionContent>
          <div className="rail-row">
            <ChatCircleText weight="duotone" />
            <div>
              <strong>{project.agent}</strong>
              <span>Opened {project.createdAt}</span>
            </div>
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  )
}

export default App
